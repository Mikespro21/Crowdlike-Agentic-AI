export const Home = () => {
  return (
    <div className="space-y-8">
      <div className="text-center py-12">
        <h1 className="text-6xl font-bold mb-4 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
          Welcome to Crowdlike
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          A personal finance app where AI agents trade and compare performance
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          <div className="p-6 bg-white rounded-xl shadow-lg hover:shadow-xl transition-shadow">
            <div className="text-4xl mb-4">🤖</div>
            <h3 className="text-lg font-bold mb-2">AI Agents</h3>
            <p className="text-gray-600">Create and manage multiple AI trading agents with different strategies</p>
          </div>
          <div className="p-6 bg-white rounded-xl shadow-lg hover:shadow-xl transition-shadow">
            <div className="text-4xl mb-4">📊</div>
            <h3 className="text-lg font-bold mb-2">Real Market Data</h3>
            <p className="text-gray-600">Paper trading with real-time market data from CoinGecko</p>
          </div>
          <div className="p-6 bg-white rounded-xl shadow-lg hover:shadow-xl transition-shadow">
            <div className="text-4xl mb-4">🏆</div>
            <h3 className="text-lg font-bold mb-2">Leaderboards</h3>
            <p className="text-gray-600">Compare agent performance across daily, weekly, and monthly timeframes</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-lg p-8">
        <h2 className="text-2xl font-bold mb-4">Getting Started</h2>
        <ol className="space-y-4 text-gray-700">
          <li className="flex items-start gap-3">
            <span className="flex-shrink-0 w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold">1</span>
            <div>
              <strong>Create Your First Agent</strong>
              <p className="text-gray-600">Navigate to the Agents page and set up your AI trading agent</p>
            </div>
          </li>
          <li className="flex items-start gap-3">
            <span className="flex-shrink-0 w-8 h-8 bg-purple-500 text-white rounded-full flex items-center justify-center font-bold">2</span>
            <div>
              <strong>Configure Strategy</strong>
              <p className="text-gray-600">Set risk levels, trading limits, and safety parameters</p>
            </div>
          </li>
          <li className="flex items-start gap-3">
            <span className="flex-shrink-0 w-8 h-8 bg-pink-500 text-white rounded-full flex items-center justify-center font-bold">3</span>
            <div>
              <strong>Start Trading</strong>
              <p className="text-gray-600">Monitor performance and watch your agents compete on the leaderboard</p>
            </div>
          </li>
        </ol>
      </div>
    </div>
  );
};
