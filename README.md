# tradingview-pine-script


MACD + KC trategy
```js
// This Pine Script® code is subject to the terms of the Mozilla Public License 2.0 at https://mozilla.org/MPL/2.0/
// © jacob_hsu

//@version=4
strategy("MACD trategy with KC Upper Exit", overlay=true, default_qty_type=strategy.percent_of_equity, default_qty_value=100, pyramiding=0)

// === MACD ===
macdFast    = input.int(12, title="MACD Fast Length")
macdSlow    = input.int(26, title="MACD Slow Length")
macdSignal  = input.int(9,  title="MACD Signal Smoothing")
[macdLine, signalLine, _] = ta.macd(close, macdFast, macdSlow, macdSignal)
goldenCross = ta.crossover(macdLine, signalLine)

// === Keltner Channel ===
kcEmaLength  = input.int(20, title="KC EMA Length")
kcAtrLength  = input.int(10, title="KC ATR Length")
kcMultiplier = input.float(1.5, title="KC Multiplier")

kcBasis   = ta.ema(close, kcEmaLength)
kcRange   = ta.atr(kcAtrLength)
kcUpper   = kcBasis + kcMultiplier * kcRange
kcLower   = kcBasis - kcMultiplier * kcRange

// === 持倉狀態判斷 ===
inLong = strategy.position_size > 0
noPosition = strategy.position_size == 0

// === 進場：MACD 黃金交叉（空倉時） ===
if (goldenCross and noPosition)
    strategy.entry("Long", strategy.long)

// === 出場：價格突破 KC 上軌（持倉中） ===
if (inLong and close > kcUpper)
    strategy.close("Long")

// === 顯示訊號與 KC 線條 ===
plotshape(goldenCross and noPosition, title="Buy", location=location.belowbar, color=color.green, style=shape.labelup, text="Buy")
plotshape(inLong and close > kcUpper, title="Sell", location=location.abovebar, color=color.red, style=shape.labeldown, text="Sell")

plot(kcUpper, title="KC Upper", color=color.gray)
plot(kcBasis, title="KC Basis", color=color.orange)

```
