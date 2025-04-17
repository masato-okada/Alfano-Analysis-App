// types.ts

export interface AnalysisSummary {
    rows: number;
    columns: number;
    missing_values: number;
  }
  
  export interface DataSample {
    [key: string]: string | number;
  }
  
  export interface ClusterSizes {
    [key: string]: number;
  }
  
  export interface ClusterMeans {
    [key: string]: {
      [key: string]: number;
    };
  }
  
  export interface SectorSummaryItem {
    sector: number;
    mean_time: number;
    max_time: number;
    min_time: number;
    mean_speed: number;
    max_speed: number;
    min_speed: number;
  }
  
  export interface SectorPoint {
    x: number;
    y: number;
    Time_sec: number;
    Sector: number;
  }
  
  export interface LapData {
    lap: number;
    sectorTimes: Record<string, number>;
    points: SectorPoint[];
  }
  
  export interface AnalysisData {
    summary: AnalysisSummary;
    columns: string[];
    data_sample: DataSample[];
    clusters?: {
      count: number;
      sizes: ClusterSizes;
      cluster_means: ClusterMeans;
    };
    sector_summary?: SectorSummaryItem[];
  }
  