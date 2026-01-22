import { TrendingUp, TrendingDown } from 'lucide-react';

export const Market = () => {
  const markets = [
    { symbol: 'BTC', name: 'Bitcoin', price: '$42,150', change: '+5.2%', trend: 'up' },
    { symbol: 'ETH', name: 'Ethereum', price: '$2,245', change: '+3.8%', trend: 'up' },
    { symbol: 'SOL', name: 'Solana', price: '$98.50', change: '-1.2%', trend: 'down' },
    { symbol: 'ADA', name: 'Cardano', price: '$0.52', change: '+2.1%', trend: 'up' },
    { symbol: 'DOT', name: 'Polkadot', price: '$7.35', change: '-0.8%', trend: 'down' },
    { symbol: 'AVAX', name: 'Avalanche', price: '$35.20', change: '+7.5%', trend: 'up' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-4xl font-bold">Market Overview</h1>
        <div className="flex gap-3">
          <button className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium transition-colors">
            Refresh
          </button>
          <button className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors">
            Paper Trade
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {markets.map((market, idx) => (
          <div key={idx} className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-gradient-to-br from-orange-400 to-yellow-500 rounded-full flex items-center justify-center text-white font-bold">
                  {market.symbol[0]}
                </div>
                <div>
                  <h3 className="text-xl font-bold">{market.symbol}</h3>
                  <p className="text-sm text-gray-600">{market.name}</p>
                </div>
              </div>
              {market.trend === 'up' ? (
                <TrendingUp className="w-6 h-6 text-green-600" />
              ) : (
                <TrendingDown className="w-6 h-6 text-red-600" />
              )}
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-end">
                <span className="text-sm text-gray-600">Current Price</span>
                <span className="text-2xl font-bold">{market.price}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">24h Change</span>
                <span className={`text-lg font-bold ${
                  market.trend === 'up' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {market.change}
                </span>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-200 flex gap-3">
              <button className="flex-1 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium transition-colors">
                Buy
              </button>
              <button className="flex-1 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-colors">
                Sell
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-4">Market Sentiment</h2>
        <div className="grid grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-4xl mb-2">📈</div>
            <p className="text-3xl font-bold text-green-600">65%</p>
            <p className="text-gray-600">Bullish</p>
          </div>
          <div className="text-center">
            <div className="text-4xl mb-2">↔️</div>
            <p className="text-3xl font-bold text-gray-600">20%</p>
            <p className="text-gray-600">Neutral</p>
          </div>
          <div className="text-center">
            <div className="text-4xl mb-2">📉</div>
            <p className="text-3xl font-bold text-red-600">15%</p>
            <p className="text-gray-600">Bearish</p>
          </div>
        </div>
      </div>
    </div>
  );
};
