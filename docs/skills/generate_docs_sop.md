# Generate Documentation Skill SOP

## Overview
自动生成项目文档，使用LLM分析代码并生成文档

## Prerequisites
- Project source code access
- filesystem tool access

## Steps

### Step 1: Analyze Project Structure
- **Action**: Read project files to understand structure
- **Tools**: filesystem
- **Input**: {"operation": "list", "path": "."}
- **Output**: Project file tree
- **Error Handling**: Use current directory if path not specified

### Step 2: Read Source Code Files
- **Action**: Read key source files for analysis
- **Tools**: filesystem
- **Input**: {"operation": "read", "path": "source_file_path"}
- **Output**: Source code content
- **Error Handling**: Skip files that cannot be read

### Step 3: Extract API Information
- **Action**: Use LLM reasoning to parse functions, classes, and APIs
- **Tools**: None (LLM analysis)
- **Input**: Source code from Step 2
- **Output**: API structure and descriptions
- **Error Handling**: Mark unclear parts as "TODO"

### Step 4: Generate Documentation
- **Action**: Use LLM to create formatted markdown documentation
- **Tools**: None (LLM generation)
- **Input**: Extracted API information
- **Output**: Markdown documentation content
- **Error Handling**: Use simple format if complex structure fails

### Step 5: Write Documentation Files
- **Action**: Save generated docs to files
- **Tools**: filesystem
- **Input**: {"operation": "write", "path": "docs/API.md", "content": "..."}
- **Output**: File paths of created documents
- **Error Handling**: Report write failures

## Expected Final Output
List of generated documentation files with paths
