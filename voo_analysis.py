"""
Анализ средней годовой доходности ETF VOO за последние 10 лет
Данные получены из Yahoo Finance
"""

import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

def calculate_annual_returns(ticker_symbol, years=10):
    """
    Вычисляет среднюю годовую доходность для заданного тикера за указанное количество лет
    
    Parameters:
    ticker_symbol (str): Символ тикера (например, 'VOO')
    years (int): Количество лет для анализа (по умолчанию 10)
    
    Returns:
    dict: Словарь с результатами анализа
    """
    # Вычисляем дату начала (10 лет назад от сегодня)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)
    
    print(f"Загрузка данных для {ticker_symbol}...")
    print(f"Период: {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}")
    
    # Загружаем данные из Yahoo Finance
    ticker = yf.Ticker(ticker_symbol)
    data = ticker.history(start=start_date, end=end_date)
    
    if data.empty:
        raise ValueError(f"Не удалось загрузить данные для {ticker_symbol}")
    
    # Получаем цену закрытия
    prices = data['Close']
    
    # Вычисляем общую доходность за весь период
    initial_price = prices.iloc[0]
    final_price = prices.iloc[-1]
    total_return = (final_price / initial_price) - 1
    
    # Вычисляем среднюю годовую доходность (CAGR - Compound Annual Growth Rate)
    num_years = (prices.index[-1] - prices.index[0]).days / 365.25
    cagr = (final_price / initial_price) ** (1 / num_years) - 1
    
    # Вычисляем доходность по годам
    annual_returns = []
    prices_df = pd.DataFrame(prices)
    prices_df['Year'] = prices_df.index.year
    
    for year in range(int(start_date.year), int(end_date.year) + 1):
        year_data = prices_df[prices_df['Year'] == year]
        if len(year_data) > 0:
            year_start_price = year_data['Close'].iloc[0]
            year_end_price = year_data['Close'].iloc[-1]
            year_return = (year_end_price / year_start_price) - 1
            annual_returns.append({
                'Year': year,
                'Return': year_return,
                'Start_Price': year_start_price,
                'End_Price': year_end_price
            })
    
    # Средняя годовая доходность (простое среднее по годам)
    avg_annual_return = sum([r['Return'] for r in annual_returns]) / len(annual_returns) if annual_returns else 0
    
    # Формируем результаты
    results = {
        'ticker': ticker_symbol,
        'start_date': prices.index[0],
        'end_date': prices.index[-1],
        'initial_price': initial_price,
        'final_price': final_price,
        'total_return': total_return,
        'cagr': cagr,
        'avg_annual_return': avg_annual_return,
        'annual_returns': annual_returns,
        'num_years': num_years
    }
    
    return results

def calculate_monthly_downside_deviation(ticker_symbol, years=10, mar=0.0):
    """
    Вычисляет месячную downside deviation (волатильность только отрицательных доходностей)
    по дневным данным за указанный период.
    
    Parameters:
    ticker_symbol (str): Символ тикера (например, 'VOO')
    years (int): Количество лет для анализа (по умолчанию 10)
    mar (float): Минимально приемлемая доходность (MAR), по умолчанию 0 (0%)
    
    Returns:
    dict: Словарь с результатами анализа
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)
    
    print(f"\nЗагрузка данных для расчёта downside deviation {ticker_symbol}...")
    print(f"Период: {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}")
    
    ticker = yf.Ticker(ticker_symbol)
    data = ticker.history(start=start_date, end=end_date)
    
    if data.empty:
        raise ValueError(f"Не удалось загрузить данные для {ticker_symbol}")
    
    prices = data['Close']
    
    # Дневные доходности
    daily_returns = prices.pct_change().dropna()
    if daily_returns.empty:
        raise ValueError("Недостаточно данных для расчёта дневных доходностей")
    
    returns_df = pd.DataFrame(daily_returns, columns=['Return'])
    returns_df['Year'] = returns_df.index.year
    returns_df['Month'] = returns_df.index.month
    
    monthly_downside = []
    
    # Группируем по годам и месяцам и считаем downside deviation по дням внутри месяца
    for (year, month), group in returns_df.groupby(['Year', 'Month']):
        period_returns = group['Return']
        if len(period_returns) == 0:
            continue
        
        downside_returns = period_returns[period_returns < mar]
        
        # Стандартная формула downside deviation:
        # sqrt( sum( min(0, r_i - MAR)^2 ) / N ), где N — количество наблюдений в периоде
        if downside_returns.empty:
            downside_dev = 0.0
        else:
            downside_dev = (((downside_returns - mar) ** 2).sum() / len(period_returns)) ** 0.5
        
        monthly_downside.append({
            'Year': year,
            'Month': month,
            'Downside_Deviation': downside_dev
        })
    
    results = {
        'ticker': ticker_symbol,
        'start_date': daily_returns.index[0],
        'end_date': daily_returns.index[-1],
        'mar': mar,
        'monthly_downside_deviation': monthly_downside
    }
    
    return results

def print_results(results):
    """Красиво выводит результаты анализа"""
    print("\n" + "="*60)
    print(f"АНАЛИЗ ДОХОДНОСТИ ETF {results['ticker']}")
    print("="*60)
    print(f"\nПериод анализа:")
    print(f"  Начало: {results['start_date'].strftime('%Y-%m-%d')}")
    print(f"  Конец:  {results['end_date'].strftime('%Y-%m-%d')}")
    print(f"  Длительность: {results['num_years']:.2f} лет")
    
    print(f"\nЦены:")
    print(f"  Начальная цена: ${results['initial_price']:.2f}")
    print(f"  Конечная цена:  ${results['final_price']:.2f}")
    
    print(f"\nДоходность:")
    print(f"  Общая доходность за период: {results['total_return']*100:.2f}%")
    print(f"  CAGR (средняя годовая доходность): {results['cagr']*100:.2f}%")
    print(f"  Средняя годовая доходность (простое среднее): {results['avg_annual_return']*100:.2f}%")
    
    print(f"\nДоходность по годам:")
    print(f"{'Год':<8} {'Начало':<12} {'Конец':<12} {'Доходность':<15}")
    print("-" * 50)
    for ret in results['annual_returns']:
        print(f"{ret['Year']:<8} ${ret['Start_Price']:<11.2f} ${ret['End_Price']:<11.2f} {ret['Return']*100:>10.2f}%")
    
    print("\n" + "="*60)

def print_monthly_downside_deviation(results):
    """Красиво выводит месячную downside deviation"""
    print("\n" + "="*60)
    print(f"МЕСЯЧНАЯ DOWNSIDE DEVIATION ETF {results['ticker']}")
    print("="*60)
    print(f"\nПериод анализа:")
    print(f"  Начало: {results['start_date'].strftime('%Y-%m-%d')}")
    print(f"  Конец:  {results['end_date'].strftime('%Y-%m-%d')}")
    print(f"  MAR (минимально приемлемая доходность): {results['mar']*100:.2f}%")
    
    print(f"\nDownside deviation по месяцам (по дневным данным):")
    print(f"{'Год':<8} {'Месяц':<8} {'Downside dev':<15}")
    print("-" * 40)
    for row in results['monthly_downside_deviation']:
        print(f"{row['Year']:<8} {row['Month']:<8} {row['Downside_Deviation']*100:>10.2f}%")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    try:
        # Анализируем VOO за последние 10 лет
        results = calculate_annual_returns('VOO', years=10)
        print_results(results)
        
        # Сохраняем результаты в CSV
        annual_returns_df = pd.DataFrame(results['annual_returns'])
        annual_returns_df.to_csv('voo_annual_returns.csv', index=False)
        print(f"\nДанные по годовым доходностям сохранены в voo_annual_returns.csv")
        
        # Расчитываем downside deviation по месяцам за последние 10 лет
        downside_results = calculate_monthly_downside_deviation('VOO', years=10, mar=0.0)
        print_monthly_downside_deviation(downside_results)
        
        # Сохраняем месячную downside deviation в CSV
        monthly_dd_df = pd.DataFrame(downside_results['monthly_downside_deviation'])
        monthly_dd_df.to_csv('voo_monthly_downside_deviation.csv', index=False)
        print(f"\nДанные по месячной downside deviation сохранены в voo_monthly_downside_deviation.csv")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
