import { useState, type HTMLAttributes } from 'react'

interface Props extends HTMLAttributes<HTMLElement> {
  language: string
  code: string
}

export default function CodeBlock({ language, code, className, ...props }: Props) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="code-block-wrapper">
      {language && <span className="code-block-lang">{language}</span>}
      <button
        className="code-copy-btn"
        onClick={handleCopy}
        title="Copy code"
      >
        {copied ? 'Copied!' : 'Copy'}
      </button>
      <pre>
        <code className={className} {...props}>{code}</code>
      </pre>
    </div>
  )
}
