export const Analytics = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-4xl font-bold">Analytics</h1>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[
          { label: 'Total Return', value: '+12.5%', emoji: '📊' },
          { label: 'Sharpe Ratio', value: '1.85', emoji: '📈' },
          { label: 'Win Rate', value: '68%', emoji: '🎯' },
          { label: 'Max Drawdown', value: '-5.2%', emoji: '📉' },
        ].map((metric, idx) => (
          <div key={idx} className="bg-white rounded-xl shadow-lg p-6">
            <div className="text-3xl mb-2">{metric.emoji}</div>
            <p className="text-3xl font-bold mb-1">{metric.value}</p>
            <p className="text-gray-600">{metric.label}</p>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-4">Performance Over Time</h2>
        <div className="h-80 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg flex items-center justify-center">
          <p className="text-gray-500">Interactive chart would display here</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-2xl font-bold mb-4">Asset Allocation</h2>
          <div className="h-64 bg-gradient-to-br from-green-50 to-blue-50 rounded-lg flex items-center justify-center">
            <p className="text-gray-500">Pie chart visualization</p>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-2xl font-bold mb-4">Agent Comparison</h2>
          <div className="h-64 bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg flex items-center justify-center">
            <p className="text-gray-500">Bar chart visualization</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-4">Risk Metrics</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { metric: 'Volatility', value: '12.3%', status: 'Medium' },
            { metric: 'Beta', value: '0.85', status: 'Low' },
            { metric: 'VaR (95%)', value: '-3.2%', status: 'Low' },
          ].map((item, idx) => (
            <div key={idx} className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-1">{item.metric}</p>
              <p className="text-2xl font-bold mb-2">{item.value}</p>
              <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                {item.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
