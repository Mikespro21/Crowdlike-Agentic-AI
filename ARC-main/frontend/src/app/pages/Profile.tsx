import { User, Settings, Bell, Lock } from 'lucide-react';

export const Profile = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-4xl font-bold">Profile</h1>

      <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl shadow-lg p-8 text-white">
        <div className="flex items-center gap-6">
          <div className="w-24 h-24 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center">
            <User className="w-12 h-12" />
          </div>
          <div>
            <h2 className="text-3xl font-bold mb-2">Demo User</h2>
            <p className="text-blue-100">demo@crowdlike.app</p>
            <p className="text-sm text-blue-100 mt-2">Member since January 2026</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center gap-3 mb-6">
            <Settings className="w-6 h-6 text-gray-600" />
            <h2 className="text-2xl font-bold">Account Settings</h2>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Display Name</label>
              <input 
                type="text" 
                defaultValue="Demo User" 
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
              <input 
                type="email" 
                defaultValue="demo@crowdlike.app" 
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <button className="w-full px-4 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors">
              Save Changes
            </button>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center gap-3 mb-6">
            <Bell className="w-6 h-6 text-gray-600" />
            <h2 className="text-2xl font-bold">Notifications</h2>
          </div>
          <div className="space-y-4">
            {[
              { label: 'Trade Alerts', enabled: true },
              { label: 'Performance Updates', enabled: true },
              { label: 'Safety Triggers', enabled: true },
              { label: 'Weekly Summary', enabled: false },
            ].map((item, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="font-medium">{item.label}</span>
                <div className={`w-12 h-6 rounded-full relative cursor-pointer transition-colors ${
                  item.enabled ? 'bg-green-500' : 'bg-gray-300'
                }`}>
                  <div className={`w-5 h-5 bg-white rounded-full absolute top-0.5 transition-transform ${
                    item.enabled ? 'right-0.5' : 'left-0.5'
                  }`}></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="flex items-center gap-3 mb-6">
          <Lock className="w-6 h-6 text-gray-600" />
          <h2 className="text-2xl font-bold">Security</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-4 border border-gray-200 rounded-lg">
            <h3 className="font-bold mb-2">Password</h3>
            <p className="text-sm text-gray-600 mb-3">Last changed 30 days ago</p>
            <button className="text-blue-500 hover:text-blue-600 font-medium text-sm">
              Change Password
            </button>
          </div>
          <div className="p-4 border border-gray-200 rounded-lg">
            <h3 className="font-bold mb-2">Two-Factor Auth</h3>
            <p className="text-sm text-gray-600 mb-3">Not enabled</p>
            <button className="text-blue-500 hover:text-blue-600 font-medium text-sm">
              Enable 2FA
            </button>
          </div>
          <div className="p-4 border border-gray-200 rounded-lg">
            <h3 className="font-bold mb-2">API Keys</h3>
            <p className="text-sm text-gray-600 mb-3">0 active keys</p>
            <button className="text-blue-500 hover:text-blue-600 font-medium text-sm">
              Manage Keys
            </button>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-4">Subscription</h2>
        <div className="flex items-center justify-between p-6 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg">
          <div>
            <h3 className="text-xl font-bold mb-1">Pro Plan</h3>
            <p className="text-gray-600">Unlimited agents • Advanced analytics • Priority support</p>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold">$49</p>
            <p className="text-sm text-gray-600">per month</p>
          </div>
        </div>
      </div>
    </div>
  );
};
