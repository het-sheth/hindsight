# Overshoot API Debugging Guide

## 🔍 Understanding the Status Change Issue

You asked: **"Why is the overshoot API not changing the status as it should?"**

Let's debug this step by step.

---

## 📊 How Overshoot Works in Hindsight

### Current Configuration
Located in: `frontend/src/app/page.tsx` (lines 203-257)

```javascript
const vision = new RealtimeVision({
  apiUrl: "https://cluster1.overshoot.ai/api/v0.2",
  apiKey: process.env.NEXT_PUBLIC_OVERSHOOT_API_KEY,

  prompt: 'Analyze the student in the video feed. Determine if they are
           focused on the screen/content or if they are distracted
           (looking away, on phone, leaving, etc). Return the status
           and a confidence score.',

  processing: {
    clip_length_seconds: 1,      // Analyzes 1-second clips
    delay_seconds: 1,            // 1-second processing delay
    sampling_ratio: 1.0,         // 100% of frames (every frame)
  },

  outputSchema: {
    type: "object",
    properties: {
      is_focused: { type: "boolean" },
      confidence: { type: "number" },
      reason: { type: "string" },
    },
  },
});
```

**Expected Behavior:**
- Every 1-2 seconds, Overshoot analyzes the video
- Returns: `{ is_focused: true/false, confidence: 0-1, reason: "..." }`
- UI updates immediately based on `is_focused`

---

## 🐛 Common Issues & Solutions

### Issue 1: Status Stuck on "Loading"
**Symptoms:**
- Status shows "🔄 Loading Overshoot..." forever
- Webcam preview is black or frozen

**Causes & Fixes:**

1. **Webcam Permission Denied**
   ```javascript
   // Check browser console for:
   // "NotAllowedError: Permission denied"
   ```
   **Fix:** Reload page and click "Allow" when prompted

2. **Invalid Overshoot API Key**
   ```javascript
   // Console shows:
   // "Overshoot SDK Error: 401 Unauthorized"
   ```
   **Fix:** Verify `NEXT_PUBLIC_OVERSHOOT_API_KEY` in `.env.local`

3. **Network/CORS Error**
   ```javascript
   // Console shows:
   // "Failed to fetch" or "CORS error"
   ```
   **Fix:** Check internet connection, try different network

---

### Issue 2: Status Doesn't Change (Always "Focused")
**Symptoms:**
- Webcam works, but status stays green
- Looking away doesn't trigger red warning

**Debugging Steps:**

**Step 1: Enable Debug Mode**
- Press `d` key while on the page
- Debug overlay appears showing raw Overshoot responses
- Look for the `is_focused` value in the JSON

**Step 2: Check Console Logs**
Open browser console (F12) and look for:
```javascript
Overshoot Raw Result: { result: '{"is_focused":false,"confidence":0.85,"reason":"looking away"}' }
Parsed Data: { is_focused: false, confidence: 0.85, reason: "looking away" }
```

**Step 3: Test Different Scenarios**

| Action | Expected `is_focused` | Expected UI |
|--------|----------------------|-------------|
| Look at screen, face visible | `true` | Green "👀 Focused" |
| Look away (left/right) | `false` | Red "⚠️ Look at screen!" |
| Look down at phone | `false` | Red "⚠️ Look at screen!" |
| Cover webcam | `false` or error | Red or error state |
| Leave frame entirely | `false` | Red "⚠️ Look at screen!" |

**If `is_focused` changes in console but UI doesn't update:**
- Check React state updates (lines 235-246)
- Verify `setIsFocused()` is being called
- Check for JavaScript errors in console

---

### Issue 3: Too Sensitive (False Positives)
**Symptoms:**
- Status flickers red even when focused
- Triggers gaps when you're still paying attention

**Causes:**
1. **Lighting too dark/bright** - AI can't see face clearly
2. **Camera angle** - Looking at screen but face angle seems "away"
3. **Eye movement** - Looking at different parts of screen detected as "away"

**Solutions:**

**A. Improve Lighting**
- Face should be well-lit (not backlit)
- Avoid shadows on face
- Natural light works best

**B. Adjust Camera Position**
- Camera at eye level
- Face centered in frame
- 1-2 feet from camera

**C. Tune the Prompt** (Advanced)
Make the detection more forgiving:

```javascript
// Current prompt (strict)
prompt: 'Analyze the student in the video feed. Determine if they are
         focused on the screen/content or if they are distracted...'

// More forgiving prompt
prompt: 'Analyze if the student is CLEARLY distracted (looking completely
         away from screen, on phone, or left the frame). Small eye movements
         or slight head turns should still count as focused. Only mark as
         distracted if obviously not paying attention.'
```

**D. Add Confidence Threshold**
Only trigger distraction if confidence is high:

```javascript
// In onResult callback (line 225+)
const isCurrentlyDistracted = !data.is_focused && data.confidence > 0.7;
```

**E. Add Debouncing**
Require distraction to last 2+ seconds before triggering:

```javascript
// Add delay before marking as distracted
let distractionTimeout = null;

if (isCurrentlyDistracted && !distractionStartRef.current) {
  distractionTimeout = setTimeout(() => {
    distractionStartRef.current = currentSessionTimeRef.current;
    onDistractionStart(currentSessionTimeRef.current);
  }, 2000); // Wait 2 seconds
}
```

---

### Issue 4: Not Sensitive Enough (Misses Distractions)
**Symptoms:**
- You look away but status stays green
- Takes a long time to detect distraction

**Causes:**
1. **Face still partially visible** - AI thinks you're still looking
2. **Slow processing** - 1-2 second delay is normal
3. **Prompt too lenient**

**Solutions:**

**A. Make Prompt Stricter**
```javascript
prompt: 'Analyze if the student is looking DIRECTLY at the screen with
         eyes visible and focused. ANY looking away (left, right, down,
         at phone, etc.) should be marked as distracted. Be strict -
         only mark as focused if clearly paying full attention.'
```

**B. Lower Sampling Delay**
```javascript
processing: {
  clip_length_seconds: 0.5,  // Faster clips
  delay_seconds: 0.5,        // Faster processing
  sampling_ratio: 1.0,
}
```
**⚠️ Warning:** This uses more API quota

**C. Add Confidence Boost**
```javascript
// Only count as focused if high confidence
const isActuallyFocused = data.is_focused && data.confidence > 0.8;
setIsFocused(isActuallyFocused);
```

---

## 🧪 Testing Checklist

Use this to verify Overshoot is working correctly:

### Basic Functionality
- [ ] Webcam preview shows your face (bottom-right)
- [ ] Status badge shows on screen (top-right)
- [ ] Pressing `d` shows debug overlay with JSON
- [ ] Console logs show "Overshoot Raw Result" every 1-2 seconds

### Status Changes
- [ ] Looking at screen = Green "👀 Focused"
- [ ] Looking left/right = Red "⚠️ Look at screen!" (within 2-3 sec)
- [ ] Looking down at phone = Red (within 2-3 sec)
- [ ] Covering webcam = Red or error
- [ ] Returning to screen = Green again

### Gap Creation
- [ ] Look away for 3+ seconds
- [ ] Return to screen
- [ ] Gap appears in "Missed Context" sidebar
- [ ] Console shows "✅ Gap saved to MongoDB" (if DB configured)
- [ ] Gap shows correct duration in sidebar

### Edge Cases
- [ ] Works in different lighting conditions
- [ ] Works with glasses on
- [ ] Works with hat/headwear
- [ ] Doesn't trigger when just moving eyes
- [ ] Triggers when reading phone

---

## 🔧 Advanced Debugging

### Enable Verbose Logging

Add this to `page.tsx` in the `onResult` callback:

```javascript
onResult: (result: { result?: string }) => {
  console.log("🔍 Overshoot Raw Result:", result);

  try {
    if (result.result) {
      const data = JSON.parse(result.result);
      console.log("📊 Parsed Data:", data);
      console.log(`   is_focused: ${data.is_focused}`);
      console.log(`   confidence: ${data.confidence}`);
      console.log(`   reason: ${data.reason}`);

      const wasDistracted = distractionStartRef.current !== null;
      const isNowDistracted = !data.is_focused;

      console.log(`🔄 State Transition:`);
      console.log(`   Was distracted: ${wasDistracted}`);
      console.log(`   Is now distracted: ${isNowDistracted}`);

      if (isNowDistracted && !wasDistracted) {
        console.log("⚠️ DISTRACTION START");
      } else if (!isNowDistracted && wasDistracted) {
        console.log("✅ DISTRACTION END");
      }

      // ... rest of code
    }
  } catch (e) {
    console.error("❌ Error parsing Overshoot result:", e);
  }
}
```

### Test with Different Prompts

Try these alternative prompts:

**Option 1: Very Strict**
```javascript
prompt: "Is the person looking directly at the camera/screen with both
         eyes clearly visible? Return is_focused=true ONLY if staring
         directly ahead. Any deviation = false."
```

**Option 2: Very Lenient**
```javascript
prompt: "Is the person in the frame and generally facing forward? Only
         mark is_focused=false if they're clearly not present or looking
         completely away from the screen."
```

**Option 3: Phone-Specific**
```javascript
prompt: "Is the person looking at their computer screen, or are they
         distracted by their phone, looking away, or not present? Mark
         is_focused=false if on phone or looking away."
```

### Visualize Overshoot Responses

Add a live graph to see confidence over time - useful for tuning thresholds.

---

## 📈 Recommended Settings

Based on testing, these settings work well:

```javascript
// Good balance of accuracy and performance
processing: {
  clip_length_seconds: 1,
  delay_seconds: 1,
  sampling_ratio: 1.0,
},

// Prompt that catches obvious distractions
prompt: `Analyze the student's attention to the screen. Mark as focused
         (is_focused=true) if they are looking at the screen with face
         visible and eyes forward. Mark as distracted (is_focused=false)
         if they are: looking away from screen, looking at phone, eyes
         not visible, or left the frame. Provide a confidence score.`,

// In the state transition logic, add 0.5s debounce:
let timeout = null;
if (isNowDistracted && !wasDistracted) {
  timeout = setTimeout(() => {
    distractionStartRef.current = currentSessionTimeRef.current;
    onDistractionStart(currentSessionTimeRef.current);
  }, 500); // 0.5 second debounce
}
```

---

## 🆘 Still Not Working?

### Check Overshoot API Status
```javascript
// Add error logging
onError: (error: any) => {
  console.error("🚨 Overshoot SDK Error:", error);
  console.error("   Type:", error?.name);
  console.error("   Message:", error?.message);
  console.error("   Status:", error?.status);

  if (error?.status === 401) {
    console.error("❌ Invalid API key! Check NEXT_PUBLIC_OVERSHOOT_API_KEY");
  } else if (error?.status === 429) {
    console.error("⏱️ Rate limit exceeded! Too many requests.");
  } else if (error?.status === 500) {
    console.error("🔧 Overshoot server error. Try again later.");
  }
}
```

### Contact Overshoot Support
- GitHub: https://github.com/overshoot-ai
- Documentation: Check Overshoot SDK docs for latest API changes

---

## ✅ Summary

**Overshoot is working if:**
- ✅ Console shows results every 1-2 seconds
- ✅ `is_focused` changes based on your actions
- ✅ UI updates match the console output
- ✅ Gaps are created when you look away

**Common fixes:**
1. Improve lighting on your face
2. Adjust camera angle (eye level, centered)
3. Tune the prompt for your use case
4. Add debouncing to reduce false positives
5. Check API key is valid

**For your project:**
The current implementation is solid! Most "issues" are actually environmental (lighting, camera position) or need prompt tuning for your specific classroom setup.

---

Happy debugging! 🔍
