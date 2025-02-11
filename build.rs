// build.rs
use pyo3_build_config::InterpreterConfig;
use std::path::Path;
use std::env;

fn main() {
    // Get the path to the Python executable from the environment variable
    // This assumes that the environment variable "PYTHON_EXECUTABLE" is set
    // If it's not set, you'll need to set it before running cargo build
    let python_path = match env::var("PYTHON_EXECUTABLE") {
        Ok(path) => path,
        Err(_) => {
            println!("cargo:warning=PYTHON_EXECUTABLE environment variable not set. Assuming 'python'");
            "python".to_string() // Fallback to "python" if the variable is not set
        }
    };

    let config_result = InterpreterConfig::from_path(Path::new(&python_path));
    match config_result {
        Ok(_config) => {
            // Successfully created the config
        },
        Err(e) => {
            println!("cargo:warning=Failed to create InterpreterConfig: {}", e);
            // You might want to exit the build script here to prevent further errors
            // or return early to continue with a default configuration
            return;
        }
    }
    // That's it!  The pyo3-build-config crate automatically handles the rest.
}
