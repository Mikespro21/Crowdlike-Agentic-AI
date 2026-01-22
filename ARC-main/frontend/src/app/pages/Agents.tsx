import { useState } from 'react';
import { Plus, TrendingUp, TrendingDown } from 'lucide-react';

export const Agents = () => {
  const [agents] = useState([
    { id: 1, name: 'Agent Alpha', strategy: 'Aggressive', profit: '+15.3%', value: '$3,200', status: 'active' },
    { id: 2, name: 'Agent Beta', strategy: 'Conservative', profit: '+8.7%', value: '$2,800', status: 'active' },
    { id: 3, name: 'Agent Gamma', strategy: 'Balanced', profit: '+12.1%', value: '$3,450', status: 'active' },
    { id: 4, name: 'Agent Delta', strategy: 'Swing Trading', profit: '-2.3%', value: '$1,950', status: 'paused' },
  ]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-4xl font-bold">Your Agents</h1>
        <button className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:shadow-lg transition-shadow">
          <Plus className="w-5 h-5" />
          Create Agent
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {agents.map((agent) => (
          <div key={agent.id} className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-xl">
                  {agent.name[0]}
                </div>
                <div>
                  <h3 className="text-xl font-bold">{agent.name}</h3>
                  <p className="text-sm text-gray-600">{agent.strategy}</p>
                </div>
              </div>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                agent.status === 'active' 
                  ? 'bg-green-100 text-green-700' 
                  : 'bg-gray-100 text-gray-700'
              }`}>
                {agent.status}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600 mb-1">Portfolio Value</p>
                <p className="text-2xl font-bold">{agent.value}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Profit/Loss</p>
                <div className="flex items-center gap-2">
                  {agent.profit.startsWith('+') ? (
                    <TrendingUp className="w-5 h-5 text-green-600" />
                  ) : (
                    <TrendingDown className="w-5 h-5 text-red-600" />
                  )}
                  <p className={`text-2xl font-bold ${
                    agent.profit.startsWith('+') ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {agent.profit}
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-200 flex gap-3">
              <button className="flex-1 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium transition-colors">
                View Details
              </button>
              <button className="flex-1 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors">
                Configure
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
