export const Dashboard = () => {
  const stats = [
    { label: 'Total Agents', value: '5', change: '+2', emoji: '🤖' },
    { label: 'Total Portfolio Value', value: '$12,450', change: '+5.2%', emoji: '💰' },
    { label: 'Best Performer', value: 'Agent Alpha', change: '+15.3%', emoji: '🏆' },
    { label: 'Active Trades', value: '12', change: '+3', emoji: '📈' },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-4xl font-bold">Dashboard</h1>
      
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, idx) => (
          <div key={idx} className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
            <div className="flex items-center justify-between mb-2">
              <span className="text-3xl">{stat.emoji}</span>
              <span className="text-sm font-medium text-green-600">{stat.change}</span>
            </div>
            <h3 className="text-2xl font-bold mb-1">{stat.value}</h3>
            <p className="text-gray-600 text-sm">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-4">Recent Activity</h2>
        <div className="space-y-4">
          {[
            { agent: 'Agent Alpha', action: 'Bought BTC', amount: '$500', time: '5m ago' },
            { agent: 'Agent Beta', action: 'Sold ETH', amount: '$350', time: '15m ago' },
            { agent: 'Agent Gamma', action: 'Bought SOL', amount: '$200', time: '1h ago' },
          ].map((activity, idx) => (
            <div key={idx} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold">
                  {activity.agent[0]}
                </div>
                <div>
                  <p className="font-medium">{activity.agent}</p>
                  <p className="text-sm text-gray-600">{activity.action}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="font-bold">{activity.amount}</p>
                <p className="text-sm text-gray-500">{activity.time}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Performance Chart Placeholder */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-4">Portfolio Performance</h2>
        <div className="h-64 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg flex items-center justify-center">
          <p className="text-gray-500">Chart visualization would go here</p>
        </div>
      </div>
    </div>
  );
};
