import os, re
from pathlib import Path
import pandas as pd
import numpy as np

MONTHS = ["January","February","March","April","May","June",
          "July","August","September","October","November","December"]
MONTH_TO_NUM = {m:i+1 for i,m in enumerate(MONTHS)}
SEASON_MAP = {
    12:"Summer",1:"Summer",2:"Summer",
    3:"Autumn",4:"Autumn",5:"Autumn",
    6:"Winter",7:"Winter",8:"Winter",
    9:"Spring",10:"Spring",11:"Spring"
}

def load_all_csvs(folder):
    frames = []
    for f in sorted(Path(folder).glob("*.csv")):
        df = pd.read_csv(f)
        month_cols = [c for c in df.columns if c in MONTHS]
        if month_cols:
            id_cols = [c for c in df.columns if c not in month_cols]
            long_df = df.melt(id_vars=id_cols, value_vars=month_cols,
                              var_name="Month", value_name="Temperature")
            long_df["MonthNum"] = long_df["Month"].map(MONTH_TO_NUM)
            m = re.search(r"(\d{4})", f.stem)
            year = int(m.group(1)) if m else None
            long_df["Year"] = year
            frames.append(long_df[["STATION_NAME","Temperature","MonthNum","Year"]]
                          .rename(columns={"STATION_NAME":"Station"}))
        else:
            frames.append(df)
    return pd.concat(frames, ignore_index=True)

def main():
    folder = Path(__file__).parent / "temperatures"
    if not folder.exists():
        raise SystemExit("Missing temperatures folder.")

    df = load_all_csvs(folder)
    df["Temperature"] = pd.to_numeric(df["Temperature"], errors="coerce")
    df = df.dropna(subset=["Temperature"])

    # Seasonal averages
    df["Season"] = df["MonthNum"].map(SEASON_MAP)
    seasonal_avg = df.groupby("Season")["Temperature"].mean().reindex(["Summer","Autumn","Winter","Spring"])

    # Temperature range per station
    grp = df.groupby("Station")["Temperature"]
    stats = pd.DataFrame({
        "min": grp.min(),
        "max": grp.max(),
        "range": grp.max() - grp.min(),
        "std": grp.std()
    }).reset_index()

    max_range = stats["range"].max()
    range_winners = stats[stats["range"]==max_range]

    # Stability
    min_std = stats["std"].min()
    max_std = stats["std"].max()
    stable_winners = stats[stats["std"]==min_std]
    variable_winners = stats[stats["std"]==max_std]

    out_dir = Path(__file__).parent

    with open(out_dir/"average_temp.txt","w") as f:
        for season,val in seasonal_avg.items():
            if pd.notna(val):
                f.write(f"{season}: {val:.1f}°C\n")

    with open(out_dir/"largest_temp_range_station.txt","w") as f:
        for _,row in range_winners.iterrows():
            f.write(f"{row['Station']}: Range {row['range']:.1f}°C (Max: {row['max']:.1f}°C, Min: {row['min']:.1f}°C)\n")

    with open(out_dir/"temperature_stability_stations.txt","w") as f:
        for _,row in stable_winners.iterrows():
            f.write(f"Most Stable: {row['Station']}: StdDev {row['std']:.1f}°C\n")
        for _,row in variable_winners.iterrows():
            f.write(f"Most Variable: {row['Station']}: StdDev {row['std']:.1f}°C\n")

    print("Outputs written.")

if __name__ == "__main__":
    main()

