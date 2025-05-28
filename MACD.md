MACD 黃金交叉在 0 軸下方 + RSI < 50

```js
//@version=5
indicator("MACD 黃金交叉在 0 軸下方 + RSI < 50", overlay=false)

// MACD 計算
[macdLine, signalLine, _] = ta.macd(close, 12, 26, 9)

// 黃金交叉條件
goldenCross = ta.crossover(macdLine, signalLine)

// MACD 值在 0 軸下方
belowZero = macdLine < 0 and signalLine < 0

// RSI 計算（14 期）
rsi = ta.rsi(close, 14)
rsiBelow50 = rsi < 50

// 三個條件都成立才觸發
triggerAlert = goldenCross and belowZero and rsiBelow50

// 顯示訊號
plotshape(triggerAlert, title="黃金交叉 + RSI<50", location=location.belowbar, color=color.green, style=shape.labelup, text="BUY")

// 快訊條件
alertcondition(triggerAlert, title="MACD 黃金交叉 + 0 軸下 + RSI<50", message="MACD 黃金交叉發生在 0 軸下方，且 RSI 小於 50，注意進場機會")
```
