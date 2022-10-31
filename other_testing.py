symbolList=[]
for line in open('sp500.txt'):
    ticker = line.split(',')[0]
    symbolList.append(ticker)

# write the symbols to a file
f = open('sp500.txt', 'w')
for symbol in symbolList:
    f.write(symbol + '\n')
    