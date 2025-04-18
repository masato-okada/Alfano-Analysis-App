import { NextApiRequest, NextApiResponse } from 'next'
import path from 'path'
import fs from 'fs'

// 型定義
interface SessionEntry {
  Session: string
  Sector: number
  RPM: number
  ['Speed GPS']: number
  F_Gear_Ratio: number
  R_Gear_Ratio: number
  ['R_Tire_Diameter [mm]']: number
  Lap: number
}

interface SectorLapEntry {
  lap: number
  sectorTimes: {
    [sector: string]: number
  }
}

// RPMヒストグラムデータ
interface RPMHistogram {
  sector: number
  bins: number[]
  all_rpm_hist: number[]
  best_rpm_hist: number[]
}

// ギア比分析用インターフェース
interface GearAnalysisResult {
  overallSuggestedGear: number
  sectorResults: {
    sector: number
    bestGear: number
    scores: { gear: number; score: number }[]
  }[]
}

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  try {
    const dataPath = path.join(process.cwd(), 'public', 'all_sessions_combined.json')
    const sectorPath = path.join(process.cwd(), 'public', 'sector_data.json')
    
    const mainRaw = fs.readFileSync(dataPath, 'utf8')
    const sectorRaw = fs.readFileSync(sectorPath, 'utf8')
    
    const mainData: SessionEntry[] = JSON.parse(mainRaw)
    const sectorData: SectorLapEntry[] = JSON.parse(sectorRaw)
    
    const cleanData = mainData.filter(
      (row) =>
        row.Session !== null &&
        row.Sector !== null &&
        row.RPM !== null &&
        row['Speed GPS'] !== null &&
        row.F_Gear_Ratio !== null &&
        row.R_Gear_Ratio !== null &&
        row['R_Tire_Diameter [mm]'] !== null &&
        row.Lap !== null
    )
    
    const binWidth = 250
    const rpmMin = 6000
    const rpmMax = 13000
    const rpmBins = Array.from({ length: Math.floor((rpmMax - rpmMin) / binWidth) + 1 }, (_, i) => rpmMin + i * binWidth)
    
    // セクターごとのベストタイムマップを構築
    const bestSectorMap: { [sectorId: number]: { lap: number; time: number } } = {}
    const sectorWeightMap: { [sectorId: number]: number } = {}
    const sectorTotalTime: { [sectorId: number]: number } = {}
    const sectorCount: { [sectorId: number]: number } = {}
    
    sectorData.forEach((entry) => {
      const lap = entry.lap
      Object.entries(entry.sectorTimes).forEach(([sectorName, time]) => {
        const sectorId = parseInt(sectorName.replace('Sector', ''))
        
        // ベストラップの記録
        if (!bestSectorMap[sectorId] || time < bestSectorMap[sectorId].time) {
          bestSectorMap[sectorId] = { lap, time }
        }
        
        // 平均時間計算用のデータ収集
        sectorTotalTime[sectorId] = (sectorTotalTime[sectorId] || 0) + time
        sectorCount[sectorId] = (sectorCount[sectorId] || 0) + 1
      })
    })
    
    // 各セクターの平均時間を計算（重み付け用）
    Object.keys(sectorTotalTime).forEach((sectorIdStr) => {
      const sectorId = parseInt(sectorIdStr)
      sectorWeightMap[sectorId] = sectorTotalTime[sectorId] / sectorCount[sectorId]
    })
    
    const sectors = Array.from(new Set(cleanData.map((d) => d.Sector))).sort((a, b) => a - b)
    const histograms: RPMHistogram[] = []
    
    sectors.forEach((sectorId) => {
      const sectorDataAll = cleanData.filter((d) => d.Sector === sectorId)
      const bestLap = bestSectorMap[sectorId]?.lap
      const rpmAll = sectorDataAll.map((d) => d.RPM)
      const rpmBest = sectorDataAll.filter((d) => d.Lap === bestLap).map((d) => d.RPM)
      
      const histAll = countHistogram(rpmAll, rpmBins)
      const histBest = countHistogram(rpmBest, rpmBins)
      
      histograms.push({
        sector: sectorId,
        bins: rpmBins,
        all_rpm_hist: histAll,
        best_rpm_hist: histBest,
      })
    })

    // ギア比分析を行う
    const gearAnalysis = analyzeGearRatio(cleanData, sectors, bestSectorMap, sectorWeightMap, rpmBins)
    
    // レスポンスにはヒストグラムデータとギア比分析結果の両方を含める
    res.status(200).json({
      histograms,
      ...gearAnalysis
    })
  } catch (error) {
    console.error('エラー:', error)
    res.status(500).json({ error: 'データ処理中にエラーが発生しました。' })
  }
}

// ヒストグラムカウント関数
function countHistogram(data: number[], bins: number[]): number[] {
  const counts = new Array(bins.length - 1).fill(0)
  data.forEach((val) => {
    for (let i = 0; i < bins.length - 1; i++) {
      if (val >= bins[i] && val < bins[i + 1]) {
        counts[i] += 1
        break
      }
    }
  })
  return counts
}

// RPMヒストグラム重み付け関数（参照RPM分布取得）
function getReferenceRpmHist(
  data: SessionEntry[],
  sessionId: string,
  sectorId: number,
  lapId: number,
  rpmBins: number[]
): number[] | null {
  // 指定されたセッション・セクター・ラップのデータを抽出
  const refData = data.filter(
    d => d.Session === sessionId && d.Sector === sectorId && d.Lap === lapId
  )
  
  if (refData.length === 0) return null
  
  // RPMヒストグラムの作成
  const hist = countHistogram(refData.map(d => d.RPM), rpmBins)
  const total = hist.reduce((sum, val) => sum + val, 0)
  
  if (total === 0) return null
  
  // 正規化された重み付け
  return hist.map(val => val / total)
}

// タイヤ周長を計算する関数
function getTireCircumference(diameterMm: number): number {
  return Math.PI * diameterMm
}

// RPMから速度を計算する関数
function rpmToSpeedKmh(rpm: number, gearRatio: number, tireCircumMm: number): number {
  const wheelRpm = rpm / gearRatio
  const speedMps = (wheelRpm * tireCircumMm) / (60 * 1000)
  return speedMps * 3.6
}

// 仮想リアスプロケット候補を生成する関数
function generateVirtualGearRatios(currentRear: number, delta: number = 3): number[] {
  const result: number[] = []
  for (let i = currentRear - delta; i <= currentRear + delta; i++) {
    result.push(i)
  }
  return result
}

// ギア比分析関数
function analyzeGearRatio(
  data: SessionEntry[], 
  sectors: number[],
  bestSectorMap: { [sectorId: number]: { lap: number; time: number } },
  sectorWeightMap: { [sectorId: number]: number },
  rpmBins: number[]
): GearAnalysisResult {
  const sectorResults: {
    sector: number
    bestGear: number
    scores: { gear: number; score: number }[]
  }[] = []
  
  // セッションとセクターでグループ化して処理
  const sessionSectors = new Map<string, Map<number, SessionEntry[]>>()
  
  data.forEach(entry => {
    const sessionId = entry.Session
    const sectorId = entry.Sector
    
    if (!sessionSectors.has(sessionId)) {
      sessionSectors.set(sessionId, new Map())
    }
    
    const sectorMap = sessionSectors.get(sessionId)!
    if (!sectorMap.has(sectorId)) {
      sectorMap.set(sectorId, [])
    }
    
    sectorMap.get(sectorId)!.push(entry)
  })
  
  // 各セッション・セクターごとに処理
  sessionSectors.forEach((sectorMap, sessionId) => {
    sectorMap.forEach((sectorEntries, sectorId) => {
      if (sectorEntries.length === 0) return
      
      // 現在のギア比とタイヤ径を取得
      const front = sectorEntries[0].F_Gear_Ratio
      const rear = sectorEntries[0].R_Gear_Ratio
      const tireDiameter = sectorEntries[0]['R_Tire_Diameter [mm]']
      const tireCircum = getTireCircumference(tireDiameter)
      
      // 最速ラップのRPM分布を参照
      const bestLap = bestSectorMap[sectorId]?.lap
      if (!bestLap) return
      
      const refWeights = getReferenceRpmHist(data, sessionId, sectorId, bestLap, rpmBins)
      if (!refWeights) return
      
      // 仮想ギア比の生成
      const virtualTeethList = generateVirtualGearRatios(rear, 3)
      const scoreEntries: { gear: number; score: number }[] = []
      
      // 各仮想ギア比でスコアを計算
      virtualTeethList.forEach(virtualRear => {
        const virtualRatio = virtualRear / front
        
        // 加重RMSEスコアの計算
        let weightedErrorSum = 0
        let weightSum = 0
        
        sectorEntries.forEach(entry => {
          const virtualSpeed = rpmToSpeedKmh(entry.RPM, virtualRatio, tireCircum)
          const actualSpeed = entry['Speed GPS'] / 10.0  // 速度を正規化
          
          // RPMに対応する重み付けを取得
          let binIndex = -1
          for (let i = 0; i < rpmBins.length - 1; i++) {
            if (entry.RPM >= rpmBins[i] && entry.RPM < rpmBins[i + 1]) {
              binIndex = i
              break
            }
          }
          
          if (binIndex >= 0 && binIndex < refWeights.length) {
            const weight = refWeights[binIndex]
            weightedErrorSum += ((virtualSpeed - actualSpeed) ** 2) * weight
            weightSum += weight
          }
        })
        
        // 加重平均二乗誤差の平方根（Weighted RMSE）
        const weightedRmse = Math.sqrt(weightedErrorSum / (weightSum || 1))
        
        // スコアは逆数に変換（小さいRMSEほど高いスコアに）
        const score = 100 / (1 + weightedRmse)
        
        scoreEntries.push({
          gear: virtualRear,
          score: score
        })
      })
      
      // 最高スコアのギア比を取得
      const bestEntry = scoreEntries.reduce((best, current) => 
        current.score > best.score ? current : best,
        { gear: 0, score: 0 }
      )
      
      sectorResults.push({
        sector: sectorId,
        bestGear: bestEntry.gear,
        scores: scoreEntries
      })
    })
  })
  
  // 全体推奨ギア比（セクターの重要度を考慮した加重平均）
  let weightedSum = 0
  let totalWeight = 0
  
  sectorResults.forEach(result => {
    const sectorId = result.sector
    const weight = sectorWeightMap[sectorId] || 1  // 重みがない場合は1を使用
    
    weightedSum += result.bestGear * weight
    totalWeight += weight
  })
  
  const overallSuggestedGear = totalWeight > 0 ? weightedSum / totalWeight : 0
  
  return {
    overallSuggestedGear,
    sectorResults
  }
}