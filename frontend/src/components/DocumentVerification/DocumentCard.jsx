import React from 'react';

const DocumentCard = ({ files = [], selfie }) => {
  const getDocIcon = (filename) => {
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
      'pdf': '📄',
      'jpg': '🖼️',
      'jpeg': '🖼️',
      'png': '🖼️'
    };
    return icons[ext] || '📎';
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const docs = Array.isArray(files) ? files : [files];
  
  return (
    <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-6">
      <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
        📋 Selected Documents
        <span className="ml-auto text-sm font-medium text-green-600 bg-green-100 px-3 py-1 rounded-full">
          {docs.length} {docs.length === 1 ? 'file' : 'files'}
        </span>
      </h3>
      
      {docs.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <svg className="mx-auto h-16 w-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p>No documents selected</p>
        </div>
      ) : (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {docs.map((file, index) => (
            <div key={index} className="flex items-center p-4 bg-gradient-to-r from-gray-50 to-white rounded-xl border-l-4 border-blue-500 hover:shadow-md transition-all">
              <div className="flex-shrink-0 w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mr-4">
                <span className="text-2xl">{getDocIcon(file.name || file.filename)}</span>
              </div>
              
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {file.name || file.filename}
                </p>
                <p className="text-xs text-gray-500">
                  {formatFileSize(file.size || 0)}
                </p>
              </div>
              
              <div className="flex items-center space-x-2">
                <span className="px-3 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
                  {file.type?.split('/')[1]?.toUpperCase() || 'PDF'}
                </span>
                <button className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
          
          {selfie && (
            <div className="relative p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl border-2 border-purple-200">
              <div className="flex items-center">
                <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center mr-4">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-purple-900">📸 Selfie Ready</p>
                  <p className="text-sm text-purple-700">{selfie.name}</p>
                </div>
                <div className="text-right">
                  <span className="block text-xs text-green-600 font-medium">✓ Valid</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
      
      <div className="mt-6 pt-6 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>Supported: PDF, JPG, PNG</span>
          <span>Max 10MB per file</span>
        </div>
      </div>
    </div>
  );
};

export default DocumentCard;

