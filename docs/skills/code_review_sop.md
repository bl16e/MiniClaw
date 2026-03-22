# Code Review Skill SOP

## Overview
代码审查流程，使用LLM分析能力检查代码规范、潜在bug和性能问题

## Prerequisites
- Code file path or directory
- filesystem tool access

## Steps

### Step 1: Read Code Files
- **Action**: Load target code files
- **Tools**: filesystem
- **Input**: {"operation": "read", "path": "file_path"}
- **Output**: Code content
- **Error Handling**: Report if file not found

### Step 2: Analyze Code Style
- **Action**: Use LLM reasoning to check formatting and naming conventions
- **Tools**: None (LLM analysis)
- **Input**: Code content from Step 1
- **Output**: Style issues list
- **Error Handling**: Continue even if some patterns unclear

### Step 3: Identify Potential Bugs
- **Action**: Use LLM reasoning to find common bug patterns (null checks, error handling, etc.)
- **Tools**: None (LLM analysis)
- **Input**: Code content from Step 1
- **Output**: Potential bug list with line numbers
- **Error Handling**: Mark uncertain issues as "potential"

### Step 4: Performance Analysis
- **Action**: Use LLM reasoning to check for performance anti-patterns
- **Tools**: None (LLM analysis)
- **Input**: Code content from Step 1
- **Output**: Performance suggestions
- **Error Handling**: Skip if code too complex

### Step 5: Generate Report
- **Action**: Compile findings into structured report
- **Tools**: filesystem (optional, to write report file)
- **Input**: All findings from previous steps
- **Output**: Formatted review report
- **Error Handling**: Return text report if file write fails

## Expected Final Output
Structured code review report with sections: Style Issues, Potential Bugs, Performance Suggestions
