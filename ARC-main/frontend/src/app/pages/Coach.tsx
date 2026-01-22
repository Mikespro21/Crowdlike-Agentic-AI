export const Coach = () => {
  const suggestions = [
    { title: 'Diversify Your Portfolio', description: 'Consider adding more variety to reduce risk', priority: 'high' },
    { title: 'Adjust Agent Beta Risk Level', description: 'Conservative strategy may miss opportunities', priority: 'medium' },
    { title: 'Review Agent Delta Performance', description: 'Negative returns for 3 consecutive days', priority: 'high' },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-4xl font-bold">AI Coach</h1>

      <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl shadow-lg p-8 text-white">
        <div className="flex items-center gap-4 mb-4">
          <div className="text-6xl">🧠</div>
          <div>
            <h2 className="text-3xl font-bold">Your AI Trading Coach</h2>
            <p className="text-blue-100">Get personalized insights and recommendations</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-4">Today's Recommendations</h2>
        <div className="space-y-4">
          {suggestions.map((suggestion, idx) => (
            <div key={idx} className="p-4 border-l-4 rounded-lg bg-gray-50"
              style={{
                borderColor: suggestion.priority === 'high' ? '#EF4444' : '#F59E0B'
              }}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-bold text-lg mb-1">{suggestion.title}</h3>
                  <p className="text-gray-600">{suggestion.description}</p>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  suggestion.priority === 'high'
                    ? 'bg-red-100 text-red-700'
                    : 'bg-yellow-100 text-yellow-700'
                }`}>
                  {suggestion.priority}
                </span>
              </div>
              <div className="mt-3 flex gap-3">
                <button className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm font-medium transition-colors">
                  Apply Now
                </button>
                <button className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg text-sm font-medium transition-colors">
                  Learn More
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="text-4xl mb-3">💡</div>
          <h3 className="text-lg font-bold mb-2">Market Insights</h3>
          <p className="text-gray-600">BTC showing bullish pattern. Consider increasing exposure.</p>
        </div>
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="text-4xl mb-3">⚠️</div>
          <h3 className="text-lg font-bold mb-2">Risk Alert</h3>
          <p className="text-gray-600">Portfolio concentration risk detected in top 3 assets.</p>
        </div>
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="text-4xl mb-3">🎯</div>
          <h3 className="text-lg font-bold mb-2">Goal Progress</h3>
          <p className="text-gray-600">On track to hit 20% annual return target.</p>
        </div>
      </div>
    </div>
  );
};
