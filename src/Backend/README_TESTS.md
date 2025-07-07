# Unit Tests for server_enhanced.py

This directory contains comprehensive unit tests for the `server_enhanced.py` FastAPI server that converts PDF documents to accessible HTML format.

## Overview

The test suite provides comprehensive coverage of:
- ✅ **87% Code Coverage**
- ✅ **41 Test Cases**
- ✅ **All Core Functions Tested**
- ✅ **API Endpoints Tested**
- ✅ **Error Handling Tested**

## Test Structure

### Test Classes

#### `TestConfigureTesseract`
Tests the Tesseract OCR configuration function across different operating systems:
- Windows path detection
- macOS configuration
- Linux configuration
- Error handling when Tesseract is not found

#### `TestValidateFile`
Tests file validation functionality:
- Valid PDF file validation
- Invalid file type rejection
- Missing filename handling
- Case-insensitive extension checking

#### `TestSafeOcrExtract`
Tests OCR text extraction from images:
- Successful text extraction
- Empty result handling
- Exception handling
- Custom language support

#### `TestCalculateAccessibilityScore`
Tests accessibility scoring algorithm:
- Perfect accessibility score (100%)
- Images without alt text penalties
- Missing H1 title penalties
- Multiple H1 titles detection
- Tables without accessibility attributes
- Generic link text detection
- Missing section structure
- Score minimum threshold (0)

#### `TestIsBigTitle`
Tests title detection based on font size:
- Non-text block handling
- Empty lines handling
- Large font detection
- Exception handling

#### `TestProcessTextBlock`
Tests text block processing:
- Simple text processing
- Link detection and conversion
- Bullet point list creation
- Title formatting
- Empty block handling

#### `TestProcessImageBlock`
Tests image processing:
- Successful image conversion to base64
- OCR alt text generation
- Missing image handling
- Exception handling

#### `TestAPIEndpoints`
Tests FastAPI endpoints:
- Health check endpoint
- File upload validation
- File size limits
- Successful PDF conversion
- Error handling

#### `TestPdfToAccessibleHtml`
Tests the main PDF conversion function:
- Successful conversion with metadata
- Missing title handling
- Exception handling
- Document cleanup

## Requirements

The following testing dependencies are required:

```
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
httpx>=0.24.0
```

These are automatically installed when you run:
```bash
pip install -r requirements.txt
```

## Running Tests

### Method 1: Using Python Script
```bash
python run_tests.py
```

### Method 2: Using PowerShell Script (Windows)
```powershell
./run_tests.ps1
```

### Method 3: Direct pytest Commands

#### Run all tests:
```bash
python -m pytest src/Backend/test_server_enhanced.py -v
```

#### Run specific test class:
```bash
python -m pytest src/Backend/test_server_enhanced.py::TestValidateFile -v
```

#### Run specific test:
```bash
python -m pytest src/Backend/test_server_enhanced.py::TestValidateFile::test_validate_file_valid_pdf -v
```

#### Run with coverage report:
```bash
python -m pytest src/Backend/test_server_enhanced.py --cov=server_enhanced --cov-report=term-missing
```

#### Run with HTML coverage report:
```bash
python -m pytest src/Backend/test_server_enhanced.py --cov=server_enhanced --cov-report=html
```

## Test Coverage

Current test coverage: **87%**

### Covered Areas:
- ✅ File validation logic
- ✅ OCR text extraction
- ✅ Accessibility scoring algorithm
- ✅ Text and image processing
- ✅ API endpoints
- ✅ Error handling
- ✅ PDF to HTML conversion

### Uncovered Areas:
- Some platform-specific Tesseract configuration paths
- Specific error conditions in PDF processing
- Some edge cases in error handling

## Test Features

### Mocking Strategy
The tests use extensive mocking to:
- Isolate units under test
- Avoid external dependencies (Tesseract, PyMuPDF)
- Simulate various error conditions
- Test different operating system behaviors

### Test Data
Tests use synthetic data where possible:
- Mock PDF documents
- Generated test images
- Simulated file uploads
- Controlled HTML content

### Assertions
Each test includes comprehensive assertions for:
- Return values
- Function call counts
- Exception types and messages
- Side effects (logging, file operations)

## Configuration

Test configuration is managed through `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["src/Backend"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--tb=short",
    "--strict-markers",
    "--disable-warnings",
]
```

## Continuous Integration

To integrate these tests into a CI/CD pipeline:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run tests with JUnit output:
   ```bash
   python -m pytest src/Backend/test_server_enhanced.py --junitxml=test-results.xml
   ```

3. Generate coverage report:
   ```bash
   python -m pytest src/Backend/test_server_enhanced.py --cov=server_enhanced --cov-report=xml
   ```

## Troubleshooting

### Common Issues

#### Import Errors
If you encounter import errors, ensure you're running tests from the project root directory:
```bash
cd /path/to/Moonshot-Project
python -m pytest src/Backend/test_server_enhanced.py
```

#### Missing Dependencies
Install all testing dependencies:
```bash
pip install pytest pytest-asyncio pytest-cov httpx
```

#### Coverage Not Working
Ensure the module path is correct:
```bash
python -m pytest src/Backend/test_server_enhanced.py --cov=server_enhanced
```

## Adding New Tests

When adding new functionality to `server_enhanced.py`, follow these guidelines:

1. **Create a new test class** for each new function/feature
2. **Test both success and failure cases**
3. **Mock external dependencies** (file I/O, network calls, etc.)
4. **Use descriptive test names** that explain what is being tested
5. **Include edge cases** and boundary conditions
6. **Update this README** with new test information

### Example Test Template

```python
class TestNewFeature:
    """Test the new_feature function."""
    
    def test_new_feature_success(self):
        """Test successful execution of new_feature."""
        # Arrange
        input_data = "test_input"
        expected_result = "expected_output"
        
        # Act
        result = new_feature(input_data)
        
        # Assert
        assert result == expected_result
    
    def test_new_feature_error_handling(self):
        """Test error handling in new_feature."""
        with pytest.raises(Exception) as exc_info:
            new_feature(invalid_input)
        assert "error message" in str(exc_info.value)
```

## Benefits

This comprehensive test suite provides:

- **Confidence** in code changes and refactoring
- **Documentation** of expected behavior
- **Regression prevention** for bug fixes
- **Quality assurance** for new features
- **Easier debugging** when issues arise
- **Better code design** through testability requirements
