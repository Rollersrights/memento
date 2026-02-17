//! Model management for Memento Core

/// Get model dimensions (384 for all-MiniLM-L6-v2)
pub fn get_dimensions() -> usize {
    384
}

/// Get max sequence length (256 for all-MiniLM-L6-v2)
pub fn get_max_length() -> usize {
    256
}
