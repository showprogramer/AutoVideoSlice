/**
 * 评分卡片组件
 *
 * 展示单个高光片段的评分结果，包含：
 * - 总分环形进度条
 * - 推荐等级徽章
 * - 四维度得分条形图
 * - 评分总结
 */

import "./ScoreCard.css";

// 推荐等级配置
const LEVEL_CONFIG = {
  excellent: { label: "优秀", color: "#34c759", emoji: "🌟" },
  good: { label: "良好", color: "#0071e3", emoji: "👍" },
  fair: { label: "一般", color: "#ff9f0a", emoji: "📝" },
  poor: { label: "较差", color: "#ff3b30", emoji: "⚠️" },
};

// 维度名称映射
const DIMENSION_NAMES = {
  virality: "传播力",
  emotion: "情感强度",
  density: "信息密度",
  completeness: "完整性",
};

export function ScoreCard({ score, compact = false }) {
  if (!score) return null;

  const { total_score, dimensions, recommendation, summary } = score;
  const level = LEVEL_CONFIG[recommendation] || LEVEL_CONFIG.fair;

  // 计算环形进度百分比
  const percentage = (total_score / 10) * 100;

  return (
    <div className={`score-card ${compact ? "score-card--compact" : ""}`}>
      {/* 总分区域 */}
      <div className="score-card__main">
        <div
          className="score-ring"
          style={{ "--percentage": percentage, "--color": level.color }}
        >
          <svg viewBox="0 0 100 100">
            <circle className="score-ring__bg" cx="50" cy="50" r="45" />
            <circle className="score-ring__progress" cx="50" cy="50" r="45" />
          </svg>
          <div className="score-ring__value">
            <span className="score-ring__number">{total_score.toFixed(1)}</span>
            <span className="score-ring__label">分</span>
          </div>
        </div>

        <div className="score-card__info">
          <div className="score-badge" style={{ backgroundColor: level.color }}>
            <span>{level.emoji}</span>
            <span>{level.label}</span>
          </div>
          {summary && <p className="score-summary">{summary}</p>}
        </div>
      </div>

      {/* 维度详情 */}
      {!compact && dimensions && dimensions.length > 0 && (
        <div className="score-dimensions">
          {dimensions.map((dim, index) => (
            <div key={index} className="score-dimension">
              <div className="score-dimension__header">
                <span className="score-dimension__name">
                  {DIMENSION_NAMES[dim.name] || dim.name}
                </span>
                <span className="score-dimension__value">
                  {dim.score.toFixed(1)}
                </span>
              </div>
              <div className="score-dimension__bar">
                <div
                  className="score-dimension__fill"
                  style={{
                    width: `${(dim.score / 10) * 100}%`,
                    backgroundColor: getScoreColor(dim.score),
                  }}
                />
              </div>
              {dim.description && (
                <p className="score-dimension__desc">{dim.description}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// 根据分数获取颜色
function getScoreColor(score) {
  if (score >= 8) return "#34c759";
  if (score >= 6) return "#0071e3";
  if (score >= 4) return "#ff9f0a";
  return "#ff3b30";
}

export default ScoreCard;
