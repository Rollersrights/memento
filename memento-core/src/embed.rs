//! Embedding module for Memento Core
//! 
//! Provides ONNX-based text embeddings using all-MiniLM-L6-v2 model.
//! Features:
//! - Fast cold start (~150ms)
//! - 384-dimensional embeddings
//! - Mean pooling with attention mask
//! - L2 normalization

pub use crate::{embed_text, embed_batch, init_model, is_ready, get_model_info};
