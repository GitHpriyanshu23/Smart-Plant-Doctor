import type { Components } from 'react-markdown';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const components: Components = {
  h1: ({ children }) => <h1 className="text-xl font-bold text-gray-900 mb-3 mt-4 first:mt-0">{children}</h1>,
  h2: ({ children }) => <h2 className="text-lg font-bold text-gray-900 mb-2 mt-4 first:mt-0">{children}</h2>,
  h3: ({ children }) => <h3 className="text-base font-semibold text-gray-900 mb-2 mt-3 first:mt-0">{children}</h3>,
  h4: ({ children }) => <h4 className="text-sm font-semibold text-gray-900 mb-1.5 mt-2">{children}</h4>,
  p: ({ children }) => <p className="mb-2 leading-relaxed last:mb-0">{children}</p>,
  ul: ({ children }) => <ul className="list-disc pl-5 mb-3 space-y-1.5">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal pl-5 mb-3 space-y-1.5">{children}</ol>,
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  a: ({ href, children }) => (
    <a href={href} className="text-leaf-700 underline hover:text-leaf-800" target="_blank" rel="noreferrer">
      {children}
    </a>
  ),
  blockquote: ({ children }) => (
    <blockquote className="border-l-4 border-leaf-300 pl-4 my-3 text-gray-600 italic">{children}</blockquote>
  ),
  hr: () => <hr className="my-4 border-gray-200" />,
  code: ({ children }) => (
    <code className="bg-gray-100 text-gray-800 px-1.5 py-0.5 rounded text-xs font-mono">{children}</code>
  ),
};

interface MarkdownContentProps {
  content: string;
  className?: string;
}

export default function MarkdownContent({ content, className = '' }: MarkdownContentProps) {
  if (!content?.trim()) return null;

  return (
    <div className={`markdown-content text-sm text-gray-700 ${className}`}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
