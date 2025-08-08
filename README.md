# tradingview-pine-script

## indicator

MA/SMA 糾結偵測
```js
indicator("MA/SMA 糾結偵測", overlay=true)

// 均線計算
ema5 = ta.ema(close, 5), ema10 = ta.ema(close, 10), ema20 = ta.ema(close, 20)
sma5 = ta.sma(close, 5), sma10 = ta.sma(close, 10), sma20 = ta.sma(close, 20)

// 均線繪圖
plot(ema5, "EMA5", color=color.teal), plot(ema10, "EMA10", color=color.navy)
plot(sma5, "SMA5", color=color.orange), plot(sma10, "SMA10", color=color.red)

// 糾結條件
tolerance = input.float(0.003, "糾結容忍距離（比例）", step=0.001) * close
is_converging = math.abs(ema5 - ema10) < tolerance and math.abs(sma5 - sma10)  < tolerance
is_bullish = ema5 > ema10 and ema10 > ema20 and sma5 > sma10 and sma10 > sma20

// 框參數
height_pct = input.float(0.01, "框高度 ±%", step=0.001), width_bars = input.int(3, "框寬（左右K棒數）", minval=1)

// 中心點
y_cross = (ema5 + ema10 + ema20 + sma5 + sma10 + sma20) / 6

// 單行叉叉（不遮擋、不報錯）
if is_converging
    label.new(x=bar_index, y=y_cross, text="✖️", style=label.style_none, textcolor=color.black, size=size.normal, color=color.new(color.white, 100))

// 單行框框
var box b = na
if is_converging
    if not na(b)
        box.delete(b)
    b := box.new(left=bar_index - width_bars, right=bar_index + width_bars, top=y_cross * (1 + height_pct), bottom=y_cross * (1 - height_pct), border_color=is_bullish ? color.green : color.red, bgcolor=is_bullish ? color.new(color.green, 85) : color.new(color.red, 85))

// 快訊條件
alertcondition(is_converging, title="均線糾結快訊", message="📊 MA/SMA 糾結出現，可能即將變盤！")
```

MACD 零軸下上 金叉/死叉
```
indicator("EMA(12) + MACD 零軸 金叉/死叉", overlay=true)

// === Inputs ===
emaLen   = input.int(12, "EMA 期間", minval=1)
fastLen  = input.int(12, "MACD 快線 EMA", minval=1)
slowLen  = input.int(26, "MACD 慢線 EMA", minval=1)
sigLen   = input.int(9,  "MACD 訊號 EMA", minval=1)

onlyBelowZero = input.bool(true,  "僅零軸下標註金叉")
markDeath     = input.bool(true,  "僅零軸上標註死叉")

// === EMA(12) ===
ema12 = ta.ema(close, emaLen)
plot(ema12, title="EMA(12)", color=color.new(color.yellow, 0), linewidth=2)

// === MACD ===
macd   = ta.ema(close, fastLen) - ta.ema(close, slowLen)
signal = ta.ema(macd, sigLen)

// 交叉
golden = ta.crossover(macd, signal)
death  = ta.crossunder(macd, signal)

// 過濾
belowZeroOKForGolden = onlyBelowZero ? (macd < 0 and signal < 0) : true
aboveZeroOKForDeath  = (macd > 0 and signal > 0)  // 只在零軸上標註死叉

// === 在 EMA 線上標註 ===
// 金叉：⭐（貼在 ema12，僅零軸下）
plotchar(golden and belowZeroOKForGolden ? ema12 : na,
         title="金叉 ⭐ (貼 EMA)", char="⭐",
         location=location.absolute, size=size.tiny, color=color.new(color.lime, 0))

// 死叉：✖️（貼在 ema12，僅零軸上）
plotchar(markDeath and death and aboveZeroOKForDeath ? ema12 : na,
         title="死叉 ✖️ (貼 EMA)", char="✖️",
         location=location.absolute, size=size.tiny, color=color.new(color.red, 0))

// === 警報===
alertcondition(golden and belowZeroOKForGolden,
     title="MACD 金叉（僅零軸下）",
     message="MACD 金叉")

alertcondition(markDeath and death and aboveZeroOKForDeath,
     title="MACD 死叉（僅零軸上）",
     message="MACD 死叉")
```



## strategy

MACD + KC trategy

```js
strategy("KC Reversal Strategy", overlay=true)

// === MACD 設定 ===
fastLength = input.int(12, "Fast length")
slowLength = input.int(26, "Slow length")
MACDLength = input.int(9, "MACD signal length")

macd = ta.ema(close, fastLength) - ta.ema(close, slowLength)
signal = ta.ema(macd, MACDLength)
delta = macd - signal
macdDeadCross = ta.crossunder(delta, 0)

// === KC 設定 ===
kcLength = input.int(20, "KC Length")
kcMultiplier = input.float(1.5, "KC Multiplier")

basis = ta.ema(close, kcLength)
range_ = ta.atr(kcLength)
upperKC = basis + kcMultiplier * range_
lowerKC = basis - kcMultiplier * range_

// === 進場條件 ===
// 做多：突破 KC 下軌（從下方穿回來）
longCondition = ta.crossover(close, lowerKC)

// 做空條件：
// 1. 價格突破上軌
brokeUpperKC = close > upperKC
// 2. 未突破但仍在區間上軌內，且 MACD 死叉
inRangeAndDeadCross = close > basis and macdDeadCross

shortCondition = brokeUpperKC or inRangeAndDeadCross

// === 進場指令 ===
if (longCondition)
    strategy.entry("Long", strategy.long, comment="buy LE")
if (shortCondition)
    strategy.entry("Short", strategy.short, comment="sell SE")
```

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
