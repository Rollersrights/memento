use pyo3::prelude::*;
use pyo3::types::PyList;
use pyo3::wrap_pyfunction;
use once_cell::sync::Lazy;
use std::sync::Mutex;
use tokenizers::Tokenizer;
use ort::session::Session;
use ort::value::Value;

/// Global model state
static MODEL_STATE: Lazy<Mutex<ModelState>> = Lazy::new(|| {
    Mutex::new(ModelState {
        session: None,
        tokenizer: None,
        dimensions: 384,
        max_length: 256,
    })
});

struct ModelState {
    session: Option<Session>,
    tokenizer: Option<Tokenizer>,
    dimensions: usize,
    max_length: usize,
}

/// Custom error type for embedding operations
#[derive(Debug, thiserror::Error)]
pub enum EmbedError {
    #[error("Model not initialized")]
    NotInitialized,
    #[error("ONNX error: {0}")]
    Onnx(String),
    #[error("Tokenizer error: {0}")]
    Tokenizer(String),
    #[error("Inference error: {0}")]
    Inference(String),
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
}

impl From<EmbedError> for PyErr {
    fn from(err: EmbedError) -> PyErr {
        pyo3::exceptions::PyRuntimeError::new_err(err.to_string())
    }
}

/// Initialize the Rust embedding engine with ONNX model.
#[pyfunction]
fn init_model(py: Python, model_path: Option<String>) -> PyResult<PyObject> {
    let model_path = model_path.unwrap_or_else(|| {
        let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
        format!("{}/.memento/models/all-MiniLM-L6-v2.onnx", home)
    });

    let model_path = std::path::PathBuf::from(model_path);

    // Load tokenizer
    let tokenizer_path = model_path
        .parent()
        .unwrap_or(std::path::Path::new("."))
        .join("tokenizer.json");

    let tokenizer = Tokenizer::from_file(&tokenizer_path)
        .map_err(|e| EmbedError::Tokenizer(format!("Failed to load tokenizer: {}", e)))?;

    // Configure tokenizer padding and truncation
    let mut tokenizer = tokenizer;
    if let Some(params) = tokenizer.get_padding_mut() {
        params.strategy = tokenizers::PaddingStrategy::BatchLongest;
        params.pad_to_multiple_of = None;
    } else {
        tokenizer.with_padding(Some(tokenizers::PaddingParams::default()));
    }
    
    if let Some(params) = tokenizer.get_truncation_mut() {
        params.max_length = 256;
        params.strategy = tokenizers::TruncationStrategy::LongestFirst;
    } else {
        let _ = tokenizer.with_truncation(Some(tokenizers::TruncationParams::default()));
    }

    // Load ONNX model - change to model directory for external data file resolution
    let model_dir = model_path.parent()
        .ok_or_else(|| EmbedError::Io(std::io::Error::new(
            std::io::ErrorKind::InvalidInput, "Invalid model path"
        )))?;
    let model_filename = model_path.file_name()
        .and_then(|n| n.to_str())
        .ok_or_else(|| EmbedError::Io(std::io::Error::new(
            std::io::ErrorKind::InvalidInput, "Invalid model filename"
        )))?;
    
    let session = load_model_with_working_dir(model_dir, model_filename)?;

    let dimensions = 384;
    
    // Update global state
    let mut state = MODEL_STATE.lock().map_err(|e| {
        EmbedError::Inference(format!("Failed to lock model state: {}", e))
    })?;
    
    state.session = Some(session);
    state.tokenizer = Some(tokenizer);
    state.dimensions = dimensions;

    // Build result dict
    let info = pyo3::types::PyDict::new_bound(py);
    info.set_item("name", "all-MiniLM-L6-v2")?;
    info.set_item("dimensions", dimensions)?;
    info.set_item("backend", "onnx")?;
    info.set_item("version", env!("CARGO_PKG_VERSION"))?;
    info.set_item("status", "loaded")?;
    info.set_item("model_path", model_path.to_str().unwrap_or(""))?;
    
    Ok(info.into())
}

/// Load ONNX model by temporarily changing working directory to handle external data files
fn load_model_with_working_dir(model_dir: &std::path::Path, model_filename: &str) -> Result<Session, EmbedError> {
    let original_dir = std::env::current_dir()
        .map_err(|e| EmbedError::Io(e))?;
    
    // Change to model directory so external data file can be found
    std::env::set_current_dir(model_dir)
        .map_err(|e| EmbedError::Io(e))?;
    
    // Load model
    let result = Session::builder()
        .map_err(|e| EmbedError::Onnx(format!("Failed to create session builder: {}", e)))?
        .commit_from_memory(&std::fs::read(model_filename)?)
        .map_err(|e| EmbedError::Onnx(format!("Failed to load model: {}", e)));
    
    // Restore original directory
    let _ = std::env::set_current_dir(original_dir);
    
    result
}

/// Check if the model is loaded and ready.
#[pyfunction]
fn is_ready() -> bool {
    MODEL_STATE.lock()
        .map(|state| state.session.is_some() && state.tokenizer.is_some())
        .unwrap_or(false)
}

/// Get model information.
#[pyfunction]
fn get_model_info(py: Python) -> PyResult<PyObject> {
    let info = pyo3::types::PyDict::new_bound(py);
    
    if let Ok(state) = MODEL_STATE.lock() {
        info.set_item("name", "all-MiniLM-L6-v2")?;
        info.set_item("dimensions", state.dimensions)?;
        info.set_item("max_sequence_length", state.max_length)?;
        info.set_item("backend", "onnx")?;
        info.set_item("version", env!("CARGO_PKG_VERSION"))?;
        info.set_item("ready", state.session.is_some())?;
        info.set_item("status", if state.session.is_some() { "loaded" } else { "not_loaded" })?;
    } else {
        info.set_item("name", "all-MiniLM-L6-v2")?;
        info.set_item("dimensions", 384)?;
        info.set_item("max_sequence_length", 256)?;
        info.set_item("backend", "onnx")?;
        info.set_item("version", env!("CARGO_PKG_VERSION"))?;
        info.set_item("ready", false)?;
        info.set_item("status", "error")?;
    }
    
    Ok(info.into())
}

/// Embed a single text string.
#[pyfunction]
fn embed_text(py: Python, text: String) -> PyResult<PyObject> {
    let embedding = embed_text_internal(&text)?;
    let py_list = PyList::new_bound(py, embedding);
    Ok(py_list.into())
}

/// Embed multiple texts in a batch.
/// 
/// Note: Currently processes texts individually due to model batch size constraints.
/// This ensures correct results for any batch size.
#[pyfunction]
fn embed_batch(py: Python, texts: Vec<String>) -> PyResult<PyObject> {
    if texts.is_empty() {
        let empty_list = PyList::empty_bound(py);
        return Ok(empty_list.into());
    }
    
    // Process each text individually to avoid batch size constraints
    let outer_list = PyList::empty_bound(py);
    for text in texts {
        let embedding = embed_text_internal(&text)?;
        let inner_list: Bound<'_ , PyList> = PyList::new_bound(py, embedding);
        outer_list.append(inner_list)?;
    }
    
    Ok(outer_list.into())
}

/// Internal function to embed a single text
fn embed_text_internal(text: &str) -> Result<Vec<f32>, EmbedError> {
    let embeddings = embed_batch_internal(&[text.to_string()])?;
    Ok(embeddings.into_iter().next().unwrap_or_else(|| vec![0.0; 384]))
}

/// Internal function to embed a batch of texts
fn embed_batch_internal(texts: &[String]) -> Result<Vec<Vec<f32>>, EmbedError> {
    // Get model state
    let mut state = MODEL_STATE.lock().map_err(|e| {
        EmbedError::Inference(format!("Failed to lock model state: {}", e))
    })?;

    // Auto-initialize if not loaded
    if state.session.is_none() || state.tokenizer.is_none() {
        drop(state);
        
        let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
        let model_path = std::path::PathBuf::from(format!(
            "{}/.memento/models/all-MiniLM-L6-v2.onnx", home
        ));
        
        let model_dir = model_path.parent()
            .ok_or_else(|| EmbedError::Io(std::io::Error::new(
                std::io::ErrorKind::InvalidInput, "Invalid model path"
            )))?;
        
        // Load tokenizer
        let tokenizer_path = model_dir.join("tokenizer.json");

        let tokenizer = Tokenizer::from_file(&tokenizer_path)
            .map_err(|e| EmbedError::Tokenizer(format!("Failed to load tokenizer: {}", e)))?;

        let mut tokenizer = tokenizer;
        tokenizer.with_padding(Some(tokenizers::PaddingParams::default()));
        let _ = tokenizer.with_truncation(Some(tokenizers::TruncationParams::default()));

        // Load ONNX model
        let session = load_model_with_working_dir(model_dir, "all-MiniLM-L6-v2.onnx")?;

        state = MODEL_STATE.lock().map_err(|e| {
            EmbedError::Inference(format!("Failed to lock model state: {}", e))
        })?;
        
        state.session = Some(session);
        state.tokenizer = Some(tokenizer);
    }

    let tokenizer = state.tokenizer.as_ref()
        .ok_or(EmbedError::NotInitialized)?;

    // Tokenize inputs
    let encodings: Vec<_> = texts.iter()
        .map(|text| tokenizer.encode(text.clone(), true))
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| EmbedError::Tokenizer(format!("Tokenization failed: {}", e)))?;

    let batch_size = texts.len();
    let max_len = encodings.iter().map(|e| e.len()).max().unwrap_or(0);

    let session = state.session.as_mut()
        .ok_or(EmbedError::NotInitialized)?;

    // Build input tensors
    let mut input_ids = vec![0i64; batch_size * max_len];
    let mut attention_mask = vec![0i64; batch_size * max_len];
    let mut token_type_ids = vec![0i64; batch_size * max_len];

    for (i, encoding) in encodings.iter().enumerate() {
        let ids = encoding.get_ids();
        let mask = encoding.get_attention_mask();
        let type_ids = encoding.get_type_ids();
        
        for (j, &id) in ids.iter().enumerate() {
            input_ids[i * max_len + j] = id as i64;
            attention_mask[i * max_len + j] = mask[j] as i64;
            token_type_ids[i * max_len + j] = type_ids[j] as i64;
        }
    }

    // Create input tensors using the shape and data tuple format
    let input_ids_shape = vec![batch_size as i64, max_len as i64];
    let attention_mask_shape = vec![batch_size as i64, max_len as i64];
    let token_type_ids_shape = vec![batch_size as i64, max_len as i64];

    let input_ids_value = Value::from_array((input_ids_shape.clone(), input_ids.into_boxed_slice()))
        .map_err(|e| EmbedError::Onnx(format!("Failed to create input_ids value: {}", e)))?;
    
    let attention_mask_value = Value::from_array((attention_mask_shape.clone(), attention_mask.into_boxed_slice()))
        .map_err(|e| EmbedError::Onnx(format!("Failed to create attention_mask value: {}", e)))?;
    
    let token_type_ids_value = Value::from_array((token_type_ids_shape.clone(), token_type_ids.into_boxed_slice()))
        .map_err(|e| EmbedError::Onnx(format!("Failed to create token_type_ids value: {}", e)))?;

    // Run inference using named inputs
    let inputs: Vec<(&str, Value)> = vec![
        ("input_ids", input_ids_value.into()),
        ("attention_mask", attention_mask_value.into()),
        ("token_type_ids", token_type_ids_value.into()),
    ];
    
    let outputs = session.run(inputs)
        .map_err(|e| EmbedError::Inference(format!("ONNX inference failed: {}", e)))?;

    // Extract embeddings from last_hidden_state: [batch, seq_len, 384]
    // Try common output names, or just take the first one
    let output_names: Vec<&str> = outputs.iter().map(|(k, _)| k).collect();
    let output_key = if output_names.contains(&"last_hidden_state") {
        "last_hidden_state"
    } else if output_names.contains(&"output") {
        "output"
    } else if !output_names.is_empty() {
        output_names[0]
    } else {
        return Err(EmbedError::Inference("No output from model".to_string()));
    };
    
    let hidden_state_output = outputs.get(output_key)
        .ok_or_else(|| EmbedError::Inference("Failed to get output".to_string()))?;
    
    let (shape, hidden_data) = hidden_state_output.try_extract_tensor::<f32>()
        .map_err(|e| EmbedError::Inference(format!("Failed to extract tensor: {}", e)))?;
    
    let seq_len = shape[1] as usize;
    let hidden_size = shape[2] as usize;

    // Perform mean pooling with attention mask
    let mut embeddings = Vec::with_capacity(batch_size);
    
    for b in 0..batch_size {
        let mask_f32: Vec<f32> = encodings[b].get_attention_mask()
            .iter()
            .map(|&m| m as f32)
            .collect();
        
        let mut sum_embedding = vec![0.0f32; hidden_size];
        let mut mask_sum = 0.0f32;
        
        for s in 0..seq_len {
            let mask_val = mask_f32.get(s).copied().unwrap_or(0.0);
            mask_sum += mask_val;
            
            for h in 0..hidden_size {
                let idx = b * seq_len * hidden_size + s * hidden_size + h;
                let val = hidden_data[idx];
                sum_embedding[h] += val * mask_val;
            }
        }
        
        // Divide by mask sum (with epsilon to avoid division by zero)
        let mask_sum = mask_sum.max(1e-9);
        for val in &mut sum_embedding {
            *val /= mask_sum;
        }
        
        // L2 normalize
        let l2_norm: f32 = sum_embedding.iter().map(|v| v * v).sum::<f32>().sqrt();
        if l2_norm > 1e-9 {
            for val in &mut sum_embedding {
                *val /= l2_norm;
            }
        }
        
        embeddings.push(sum_embedding);
    }

    Ok(embeddings)
}

/// Memento Core - Rust embeddings for Python
#[pymodule]
fn memento_core(m: &Bound<'_ , PyModule>) -> PyResult<()> {
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    
    m.add_wrapped(wrap_pyfunction!(init_model))?;
    m.add_wrapped(wrap_pyfunction!(embed_text))?;
    m.add_wrapped(wrap_pyfunction!(embed_batch))?;
    m.add_wrapped(wrap_pyfunction!(is_ready))?;
    m.add_wrapped(wrap_pyfunction!(get_model_info))?;
    
    Ok(())
}
