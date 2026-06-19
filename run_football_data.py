from futedata.collectors.football_data import FootballDataCollector

if __name__ == "__main__":
    collector = FootballDataCollector()
    results = collector.run()
    for res in results:
        print(res)
