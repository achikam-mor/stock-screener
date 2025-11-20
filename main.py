"""
Fetch last 500 days of Open & Close prices from Yahoo Finance for all tickers in AllStocks.txt,
apply split-only adjustment, check SMA150 conditions, and calculate ATR14 for tickers that pass.
"""

import asyncio
from data_loader import DataLoader
from stock_analyzer import StockAnalyzer
from stock_screener import StockScreener
from results_manager import ResultsManager

async def main():
    # Initialize components
    data_loader = DataLoader(max_concurrent_requests=5)
    analyzer = StockAnalyzer()
    screener = StockScreener(analyzer)
    results_manager = ResultsManager()

    # Load tickers
    tickers_file = r"C:\Users\User\PycharmProjects\PythonProject\AllStocks.txt"
    tickers = ['AAUC','ABBV','AEE','AEG','AFG','AGCO','AGI','AIT','ALE','ALLE','ALLY','APAM','AQNB','ASB','ASBA','ATKR','ATO','AUB','AX','AZZ','BBAI','BCO','BDC','BEPI','BEPJ','BHP','BILL','BIP','BIPJ','BLK','BNJ','BNL','BRC','BRX','BTI','BURL','BXP','BYD','CAE','CBRE','CCZ','CDP','CIMN','CMS','CMSA','CMSC','CMSD','CNP','CNQ','CNR','COF','CPK','CR','CRC','CURB','CWEN','CWT','D','DAL','DBD','DGX','DHI','DHR','DIS','DKL','DKS','DOCS','DTG','DTM','DTW','DUK','ECCF','EGP','ELC','EMA','ENIC','ENJ','ENO','EQT','ESNT','ETSY','EVR','FE','FHI','FHN','FIHL','FLR','FNB','FNV','FRT','FSS','FTS','GAP','GDV','GENI','GEV','GFF','GHC','GJS','GL','GNRC','GOLF','GVA','HCXY','HD','HEI','HGTY','HHH','HIG','HLT','HR','HTH','ICL','IDA','IHG','IHS','INFA','IRM','IX','JBL','K','KAR','KBH','KEY','KNX','KTB','KWR','LAZ','LEN','LMT','LOW','LTM','LYV','MAC','MCO','MDT','MFAO','MFC','MHO','MKL','MMM','MNSO','MRP','MSM','MTG','MUFG','NAN','NGG','NHI','NI','NMR','NOC','NVS','NVST','NYT','OGS','OII','OR','ORI','OSCR','OSK','OUT','PAGS','PCOR','PFGC','PFH','PFS','PHIN','PHM','PKX','PMTU','PNR','PPL','PRS','PSN','R','RCB','RCC','RDN','RF','RJF','RKT','RLX','RNR','ROL','RSI','RWTN','RWTO','SCHW','SCI','SHEL','SKE','SKT','SLF','SMFG','SMR','SNA','SO','SOJC','SONY','SPNT','SREA','SSD','ST','STE','STN','STVN','SU','TDS','TDW','TFC','TFII','THG','TIC','TJX','TKO','TKR','TR','TRV','TT','TTAM','TXNM','TXT','UBER','UBS','UMC','URI','USB','VIK','VMC','VOYA','VSH','VST','WAB','WBS','WDS','WEC','WMT','WPC','WPM']

    # Fetch stock data in parallel
    stock_data, fetch_failed_tickers = await data_loader.fetch_all_stocks_data(tickers)

    # Screen stocks and combine failed tickers from both fetching and screening
    results = screener.screen_stocks(stock_data)
    results.failed_tickers.extend(fetch_failed_tickers)  # Add fetch failures to results

    # Display results
    results_manager.print_results(results)
    
    # Save results to JSON file for web display
    results_manager.save_to_json(results, len(tickers), "results.json")

if __name__ == "__main__":
    asyncio.run(main())
