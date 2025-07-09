from dependency_injector import containers, providers
from dependency_injector.wiring import inject, Provide

from src.risks.calculate_life_risk import LifeRiskCalculator
from src.risks.calculate_risk import (
    InterestRateRiskCalculator,
    RiskCalculator,
    RiskCalculatorFactory,
    SpreadRiskCalculator,
    TypicalRiskCalculator,
)
from src.risks.helpers.input_file_reader_interface import (
    CsvReader,
    ExcelReader,
    FilePathReader,
    FileReaderFactory,
)


class Container(containers.DeclarativeContainer):

    # Initialize local file readers - CSV and Excel
    csvReader = providers.Factory(CsvReader)
    excelReader = providers.Factory(ExcelReader)

    fileReaderFactory = providers.Factory(
        FileReaderFactory, readers=[csvReader(), excelReader()]
    )
    filePathReader = providers.Factory(FilePathReader, factory=fileReaderFactory)

    # Initialize all calculators

    typical_risk_calculator = providers.Factory(TypicalRiskCalculator)
    interest_rate_risk_calculator = providers.Factory(InterestRateRiskCalculator)
    spread_risk_calculator = providers.Factory(SpreadRiskCalculator)

    risk_calculator_factory = providers.Factory(
        RiskCalculatorFactory,
        [
            typical_risk_calculator(),
            interest_rate_risk_calculator(),
            spread_risk_calculator(),
        ],
    )
    base_risk_calculator = providers.Factory(RiskCalculator, risk_calculator_factory)

    life_risk_calculator = providers.Factory(LifeRiskCalculator, base_risk_calculator)


@inject
def main(
    life_risk_calculator: LifeRiskCalculator = Provide[Container.life_risk_calculator],
):
    result = life_risk_calculator.calculate_life_risk_all_subrisks("file.csv")


if __name__ == "_main_":
    container = Container()
    container.wire(modules=[__name__])
    main()
