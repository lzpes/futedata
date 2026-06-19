from futedata.validators.raw_validator import RawValidator

validator = RawValidator()
results = validator.run()

print("\nResultados da Validação:")
for source, result in results.items():
    print(f"- {source.upper()}: {result}")
