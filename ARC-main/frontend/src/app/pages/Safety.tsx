import { AlertTriangle, Shield, CheckCircle } from 'lucide-react';

export const Safety = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-4xl font-bold">Safety Controls</h1>

      <div className="bg-gradient-to-r from-red-500 to-orange-600 rounded-xl shadow-lg p-8 text-white">
        <div className="flex items-center gap-4">
          <Shield className="w-16 h-16" />
          <div>
            <h2 className="text-3xl font-bold">Risk Management</h2>
            <p className="text-red-100">Configure safety parameters and exit triggers</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold">Safety Exits</h3>
            <div className="w-12 h-6 bg-green-500 rounded-full relative cursor-pointer">
              <div className="w-5 h-5 bg-white rounded-full absolute right-0.5 top-0.5"></div>
            </div>
          </div>
          <p className="text-sm text-gray-600">Automatically sell all positions when triggers activate</p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold">Max Daily Loss</h3>
            <AlertTriangle className="w-6 h-6 text-orange-500" />
          </div>
          <div className="space-y-2">
            <p className="text-3xl font-bold">-10%</p>
            <input type="range" min="1" max="20" defaultValue="10" className="w-full" />
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold">Max Drawdown</h3>
            <AlertTriangle className="w-6 h-6 text-red-500" />
          </div>
          <div className="space-y-2">
            <p className="text-3xl font-bold">-15%</p>
            <input type="range" min="5" max="30" defaultValue="15" className="w-full" />
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-4">Active Safety Triggers</h2>
        <div className="space-y-3">
          {[
            { name: 'Max Daily Loss Trigger', threshold: '-10%', status: 'active' },
            { name: 'Max Drawdown Trigger', threshold: '-15%', status: 'active' },
            { name: 'Fraud/Anomaly Detection', threshold: 'Auto', status: 'active' },
          ].map((trigger, idx) => (
            <div key={idx} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-4">
                <CheckCircle className="w-6 h-6 text-green-600" />
                <div>
                  <p className="font-bold">{trigger.name}</p>
                  <p className="text-sm text-gray-600">Threshold: {trigger.threshold}</p>
                </div>
              </div>
              <span className="px-4 py-2 bg-green-100 text-green-700 rounded-lg font-medium">
                {trigger.status}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-4">Panic Controls</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <button className="p-6 bg-red-50 hover:bg-red-100 border-2 border-red-200 rounded-lg transition-colors">
            <AlertTriangle className="w-8 h-8 text-red-600 mx-auto mb-3" />
            <h3 className="font-bold text-lg mb-2">Panic Sell</h3>
            <p className="text-sm text-gray-600">Immediately sell all positions across all agents</p>
          </button>
          <button className="p-6 bg-orange-50 hover:bg-orange-100 border-2 border-orange-200 rounded-lg transition-colors">
            <Shield className="w-8 h-8 text-orange-600 mx-auto mb-3" />
            <h3 className="font-bold text-lg mb-2">Pause All Trading</h3>
            <p className="text-sm text-gray-600">Temporarily halt all agent trading activity</p>
          </button>
        </div>
      </div>
    </div>
  );
};
