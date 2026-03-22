# Send Email Skill SOP

## Overview
发送邮件的标准操作流程，使用系统命令或脚本

## Prerequisites
- Email address (recipient)
- Subject and body content
- Shell access

## Steps

### Step 1: Validate Email Address
- **Action**: Check if email format is valid using regex
- **Tools**: None (LLM reasoning)
- **Input**: Email address string
- **Output**: Valid/Invalid status
- **Error Handling**: If invalid, return error message to user

### Step 2: Compose Email Content
- **Action**: Prepare email subject and body
- **Tools**: filesystem (if using template)
- **Input**: Subject, body text, optional template path
- **Output**: Formatted email content
- **Error Handling**: Use simple format if template not found

### Step 3: Send Email via Shell
- **Action**: Use system mail command or SMTP
- **Tools**: shell
- **Input**: {"command": "echo 'body' | mail -s 'subject' recipient@example.com"}
- **Output**: Success confirmation or error message
- **Error Handling**: Check command exit code, report failure details

## Expected Final Output
"Email sent successfully to [recipient]" or detailed error message

