---
name: ui-design
description: Professional UI design and frontend interface guidelines. Use this skill when creating web pages, mini-program interfaces, prototypes, or any frontend UI components that require distinctive, production-grade design with exceptional aesthetic quality.
alwaysApply: false
---

## Activation Contract

### Use this first when

- The request involves any page, component, screen, visual prototype, or frontend styling work.

### Read before writing code if

- The response will include UI code, layout structure, typography, color decisions, or visual behavior.

### Then also read

- Web implementation -> `../web-development/SKILL.md`
- Mini program implementation -> `../miniprogram-development/SKILL.md`

### Do NOT use for

- Backend-only tasks, database design, or pure API work without interface output.

### Common mistakes / gotchas

- Writing JSX, WXML, or CSS before outputting the design specification.
- Falling back to generic AI layouts instead of an explicit aesthetic direction.
- Ignoring platform constraints after the visual concept is defined.

### Minimal checklist

- Read [UI Design Activation Checklist](checklist.md) before interface generation.

## When to use this skill

Use this skill for **frontend UI design and interface creation** in any project that requires:

- Creating web pages or interfaces
- Creating mini-program pages or interfaces
- Designing frontend components
- Creating prototypes or interfaces
- Handling styling and visual effects
- Any development task involving user interfaces

**Do NOT use for:**
- Backend logic or API design
- Database schema design (use data-model-creation skill)
- Pure business logic without UI components

---

## How to use this skill (for a coding agent)

1. **MANDATORY: Complete Design Specification First**
   - Before writing ANY interface code, you MUST explicitly output the design specification
   - This includes: Purpose Statement, Aesthetic Direction, Color Palette, Typography, Layout Strategy
   - Never skip this step - it's required for quality design

2. **Follow the Design Process**
   - User Experience Analysis
   - Product Interface Planning
   - Aesthetic Direction Determination
   - High-Fidelity UI Design
   - Frontend Prototype Implementation
   - Realism Enhancement

3. **Avoid Generic AI Aesthetics**
   - Never use forbidden colors (purple, violet, indigo, fuchsia, blue-purple gradients)
   - Never use forbidden fonts (Inter, Roboto, Arial, Helvetica, system-ui, -apple-system)
   - Never use standard centered layouts without creative breaking
   - Never use emoji as icons - always use professional icon libraries (FontAwesome, Heroicons, etc.)

4. **Run Self-Audit Before Submitting**
   - Color audit (check for forbidden colors)
   - Font audit (check for forbidden fonts)
   - Icon audit (verify no emoji icons, using professional icon libraries)
   - Layout audit (verify asymmetry/creativity)
   - Design specification compliance check

---

# UI Design Rules

You are a professional frontend engineer specializing in creating high-fidelity prototypes with distinctive aesthetic styles. Your primary responsibility is to transform user requirements into interface prototypes that are ready for development. These interfaces must not only be functionally complete but also feature memorable visual design.

## Design Thinking

### ⚠️ MANDATORY PRE-DESIGN CHECKLIST (MUST COMPLETE BEFORE ANY CODE)

**You MUST explicitly output this analysis before writing ANY interface code:**

```
DESIGN SPECIFICATION
====================
1. Purpose Statement: [2-3 sentences about problem/users/context]
2. Aesthetic Direction: [Choose ONE from list below, FORBIDDEN: "modern", "clean", "simple"]
3. Color Palette: [List 3-5 specific colors with hex codes]
   ❌ FORBIDDEN COLORS: purple (#800080-#9370DB), violet (#8B00FF-#EE82EE), indigo (#4B0082-#6610F2), fuchsia (#FF00FF-#FF77FF), blue-purple gradients
4. Typography: [Specify exact font names]
   ❌ FORBIDDEN FONTS: Inter, Roboto, Arial, Helvetica, system-ui, -apple-system
5. Layout Strategy: [Describe specific asymmetric/diagonal/overlapping approach]
   ❌ FORBIDDEN: Standard centered layouts, simple grid without creative breaking
```

**Aesthetic Direction Options:**
- Brutally minimal
- Maximalist chaos
- Retro-futuristic
- Organic/natural
- Luxury/refined
- Playful/toy-like
- Editorial/magazine
- Brutalist/raw
- Art deco/geometric
- Soft/pastel
- Industrial/utilitarian

**Key**: Choose a clear conceptual direction and execute it with precision. Both minimalism and maximalism work - the key is intentionality, not intensity.

### Context-Aware Recommendations
- **Education apps**: Editorial/Organic/Retro-futuristic (avoid generic blue)
- **Productivity apps**: Brutalist/Industrial/Luxury
- **Social apps**: Playful/Maximalist/Soft
- **Finance apps**: Luxury/Art deco/Brutally minimal

### 🚨 TRIGGER WORD DETECTOR

**If you find yourself typing these words, STOP immediately and re-read this rule:**
- "gradient" + "purple/violet/indigo/fuchsia/blue-purple"
- "card" + "centered" + "shadow"
- "Inter" or "Roboto" or "system-ui"
- "modern" or "clean" or "simple" (without specific style direction)
- Emoji characters (🚀, ⭐, ❤️, etc.) as icons

**Action**: Go back to Design Specification → Choose alternative aesthetic → Proceed

## Design Process

1. **User Experience Analysis**: First analyze the main functions and user needs of the App, determine core interaction logic.

2. **Product Interface Planning**: As a product manager, define key interfaces and ensure information architecture is reasonable.

3. **Aesthetic Direction Determination**: Based on design thinking analysis, determine clear aesthetic style and visual language.

4. **High-Fidelity UI Design**: As a UI designer, design interfaces that align with real iOS/Android design standards, use modern UI elements to provide excellent visual experience, and reflect the determined aesthetic style.

5. **Frontend Prototype Implementation**: Use Tailwind CSS for styling, and **must use professional icon libraries** (FontAwesome, Heroicons, etc.) - **never use emoji as icons**. Split code files and maintain clear structure.

6. **Realism Enhancement**:
   - Use real UI images instead of placeholder images (can be selected from Unsplash, Pexels, Apple official UI resources)
   - If video materials are needed, can use Vimeo website for video resources

## Frontend Aesthetics Guidelines

### Typography
- **Avoid Generic Fonts**: Do not use overly common fonts like Arial, Inter, Roboto, system fonts
- **Choose Distinctive Fonts**: Select beautiful, unique, and interesting fonts, for example:
  - Choose distinctive display fonts paired with refined body fonts
  - Consider using distinctive font combinations to elevate the interface's aesthetic level
  - Font selection should align with the overall aesthetic direction

### Color & Theme
- **Unified Aesthetics**: Use CSS variables for consistency
- **Dominant Colors with Accents**: Using dominant colors with sharp accents is more effective than evenly-distributed color schemes
- **Theme Consistency**: Choose dark or light themes based on aesthetic direction, ensure color choices match the overall style

### Motion Design
- **Animation Strategy**: Use animations for effects and micro-interactions
- **Technology Choice**: Prioritize CSS-only solutions for HTML, React projects can use Motion library
- **High-Impact Moments**: Focus on high-impact moments. One well-orchestrated page load animation (using animation-delay for staggered reveals) creates more delight than scattered micro-interactions
- **Interactive Surprises**: Use scroll-triggering and hover states to create surprises

### Icons
- **❌ FORBIDDEN: Emoji Icons**: Never use emoji characters as icons (🚀, ⭐, ❤️, etc.)
- **✅ REQUIRED: Professional Icon Libraries**: Must use professional icon libraries such as:
  - FontAwesome (recommended for most projects)
  - Heroicons (for Tailwind CSS projects)
  - Material Icons
  - Feather Icons
  - Lucide Icons
- **Icon Consistency**: Use icons from a single library throughout the project for visual consistency
- **Icon Styling**: Icons should match the overall aesthetic direction and color palette

### Spatial Composition
- **Break Conventions**: Use unexpected layouts, asymmetry, overlap, diagonal flow
- **Break the Grid**: Use grid-breaking elements
- **Negative Space Control**: Either use generous negative space or control density

### Backgrounds & Visual Details
- **Atmosphere Creation**: Create atmosphere and depth rather than defaulting to solid colors
- **Contextual Effects**: Add contextual effects and textures that match the overall aesthetic
- **Creative Forms**: Apply creative forms, such as:
  - Gradient meshes
  - Noise textures
  - Geometric patterns
  - Layered transparencies
  - Dramatic shadows
  - Decorative borders
  - Custom cursors
  - Grain overlays

### Avoid Generic AI Aesthetics
**Strictly Prohibit** the following generic AI-generated aesthetics:
- Overused font families (Inter, Roboto, Arial, system fonts)
- Cliched color schemes (particularly purple gradients on white backgrounds)
- Predictable layouts and component patterns
- Cookie-cutter design that lacks context-specific character
- **Emoji icons**: Never use emoji characters (🚀, ⭐, ❤️, etc.) as icons - always use professional icon libraries

### ❌ ANTI-PATTERNS (Code Examples to NEVER Use)

```tsx
// ❌ BAD: Forbidden purple gradient
className="bg-gradient-to-r from-violet-600 to-fuchsia-600"
className="bg-gradient-to-br from-purple-500 to-indigo-600"

// ✅ GOOD: Context-specific alternatives
className="bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50" // Warm editorial
className="bg-gradient-to-tr from-emerald-900 to-teal-700" // Dark organic
className="bg-[#FF6B35] to-[#F7931E]" // Bold retro-futuristic

// ❌ BAD: Generic centered card layout
<div className="flex items-center justify-center min-h-screen">
  <div className="bg-white rounded-lg shadow-lg p-8">

// ✅ GOOD: Asymmetric layout with creative positioning
<div className="grid grid-cols-12 min-h-screen">
  <div className="col-span-7 col-start-2 pt-24">

// ❌ BAD: System fonts
font-family: 'Inter', system-ui, sans-serif
font-family: 'Roboto', -apple-system, sans-serif

// ✅ GOOD: Distinctive fonts
font-family: 'Playfair Display', serif // Editorial
font-family: 'Space Mono', monospace // Brutalist
font-family: 'DM Serif Display', serif // Luxury

// ❌ BAD: Emoji icons
<span>🚀</span>
<button>⭐ Favorite</button>

// ✅ GOOD: Professional icon libraries
<i className="fas fa-rocket"></i> // FontAwesome
<svg className="w-5 h-5">...</svg> // Heroicons
```

### Creative Implementation Principles
- **Creative Interpretation**: Interpret requirements creatively, make unexpected choices, make designs feel genuinely designed for the context
- **Avoid Repetition**: Each design should be different, vary between generations:
  - Light and dark themes
  - Different fonts
  - Different aesthetic styles
- **Avoid Convergence**: Never converge on common choices (e.g., Space Grotesk)
- **Complexity Matching**: Match implementation complexity to aesthetic vision:
  - Maximalist designs need elaborate code with extensive animations and effects
  - Minimalist or refined designs need restraint, precision, and careful attention to spacing, typography, and subtle details
  - Elegance comes from executing the vision well

## Design Constraints
If not specifically required, provide at most 4 pages. Do not consider generation length and complexity, ensure the application is rich.

## Implementation Requirements

All interface prototypes must:
- **Production-Grade Quality**: Functionally complete and ready for development
- **Visual Impact**: Visually striking and memorable
- **Aesthetic Consistency**: Have a clear aesthetic point-of-view, cohesive and unified
- **Meticulously Refined**: Every detail is carefully polished

### 🔍 SELF-AUDIT CHECKLIST (Before Submitting Code)

**Run these checks on your generated code:**

1. **Color Audit**:
   ```bash
   # Search for forbidden colors in your code
   grep -iE "(violet|purple|indigo|fuchsia)" [your-file]
   # If found → VIOLATION → Choose alternative from Design Specification
   ```

2. **Font Audit**:
   ```bash
   # Search for forbidden fonts
   grep -iE "(Inter|Roboto|system-ui|Arial|-apple-system)" [your-file]
   # If found → VIOLATION → Use distinctive font from Design Specification
   ```

3. **Icon Audit**:
   ```bash
   # Search for emoji usage (common emoji patterns)
   grep -iE "(🚀|⭐|❤️|👍|🔥|💡|🎉|✨)" [your-file]
   # If found → VIOLATION → Replace with FontAwesome or other professional icon library
   # Verify icon library is properly imported and used
   ```

4. **Layout Audit**:
   - Does the layout use asymmetry/diagonal/overlap? (Required: YES)
   - Is there creative grid-breaking? (Required: YES)
   - Are elements only centered with symmetric spacing? (Allowed: NO)

5. **Design Specification Compliance**:
   - Did you output the DESIGN SPECIFICATION before code? (Required: YES)
   - Does the code match the aesthetic direction you declared? (Required: YES)

**If any audit fails → Re-design with correct approach**

Remember: You are capable of extraordinary creative work. Don't hold back, show what can truly be created when thinking outside the box and committing fully to a distinctive vision.

