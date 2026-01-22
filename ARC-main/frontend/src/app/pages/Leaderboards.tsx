import { Trophy, Medal, Award } from 'lucide-react';

export const Leaderboards = () => {
  const leaderboard = [
    { rank: 1, botId: 'BOT-A7X2', score: 1523, profit: '+15.3%', streak: 23 },
    { rank: 2, botId: 'BOT-B9K5', score: 1487, profit: '+14.1%', streak: 18 },
    { rank: 3, botId: 'BOT-C3M1', score: 1421, profit: '+12.7%', streak: 14 },
    { rank: 4, botId: 'BOT-D8P4', score: 1390, profit: '+11.9%', streak: 12 },
    { rank: 5, botId: 'BOT-E2N7', score: 1365, profit: '+11.2%', streak: 9 },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-4xl font-bold">Leaderboards</h1>

      <div className="flex gap-4 bg-white rounded-xl shadow-lg p-2">
        {['Daily', 'Weekly', 'Monthly', 'Yearly'].map((period) => (
          <button
            key={period}
            className={`flex-1 px-4 py-3 rounded-lg font-medium transition-colors ${
              period === 'Weekly'
                ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
                : 'hover:bg-gray-100'
            }`}
          >
            {period}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        <div className="bg-gradient-to-r from-yellow-400 via-orange-500 to-red-500 p-6 text-white">
          <div className="flex items-center gap-4">
            <Trophy className="w-16 h-16" />
            <div>
              <h2 className="text-3xl font-bold">Top Performers</h2>
              <p className="text-yellow-100">Weekly Rankings</p>
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="space-y-4">
            {leaderboard.map((entry) => {
              const getRankIcon = () => {
                if (entry.rank === 1) return <Trophy className="w-6 h-6 text-yellow-500" />;
                if (entry.rank === 2) return <Medal className="w-6 h-6 text-gray-400" />;
                if (entry.rank === 3) return <Award className="w-6 h-6 text-orange-600" />;
                return <span className="text-xl font-bold text-gray-400">#{entry.rank}</span>;
              };

              return (
                <div
                  key={entry.botId}
                  className={`flex items-center justify-between p-6 rounded-lg ${
                    entry.rank <= 3
                      ? 'bg-gradient-to-r from-yellow-50 to-orange-50 border-2 border-yellow-200'
                      : 'bg-gray-50'
                  }`}
                >
                  <div className="flex items-center gap-6">
                    <div className="w-16 flex justify-center">
                      {getRankIcon()}
                    </div>
                    <div>
                      <p className="text-xl font-bold">{entry.botId}</p>
                      <p className="text-sm text-gray-600">Score: {entry.score}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-8">
                    <div className="text-right">
                      <p className="text-sm text-gray-600">Profit</p>
                      <p className="text-xl font-bold text-green-600">{entry.profit}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-600">Streak</p>
                      <p className="text-xl font-bold">{entry.streak} days</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-4">Score Calculation</h2>
        <div className="space-y-3 text-gray-700">
          <p><strong>Formula:</strong> Score = (Profit × 100) + Streaks</p>
          <p className="text-sm text-gray-600">Profit is rounded to 2 decimals before scoring</p>
          <p className="text-sm text-gray-600">Streaks = consecutive periods with profit {'>'} 0</p>
        </div>
      </div>
    </div>
  );
};
