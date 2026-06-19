from futedata.collectors.transfermarkt import TransfermarktCollector

if __name__ == "__main__":
    collector = TransfermarktCollector(filter_brasileirao=True)
    try:
        results = collector.run()
        for res in results:
            print(res)
    finally:
        collector.close()
