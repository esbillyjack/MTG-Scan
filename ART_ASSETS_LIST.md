# Aces Pup - Art Assets List

## Overview
This document lists all the art assets needed for the Aces Pup game, with specifications for size, format, and usage.

## Image Format Requirements
- **Format**: PNG (with transparency support)
- **Color Depth**: 32-bit RGBA
- **Compression**: Lossless
- **Style**: Simple, clean, cartoon-style graphics

---

## Character Assets

### 1. Dog Pilot Sprites
**Purpose**: Main player characters in character select and gameplay

#### 1.1 Character Select Portraits
- **Rex (Beagle Male)**
  - **Size**: 200x200px
  - **Usage**: Character selection screen
  - **Style**: Headshot portrait, friendly expression
  - **Details**: Brown beagle with pilot goggles/helmet

- **Luna (Dachshund Female)**
  - **Size**: 200x200px
  - **Usage**: Character selection screen
  - **Style**: Headshot portrait, determined expression
  - **Details**: Brown dachshund with pilot scarf/helmet

- **Paco (Chihuahua Male Teen)**
  - **Size**: 200x200px
  - **Usage**: Character selection screen
  - **Style**: Headshot portrait, excited expression
  - **Details**: Brown chihuahua with pilot cap/glasses

#### 1.2 Dog Plane Sprites
**Purpose**: Player aircraft in gameplay (viewed from behind)

- **Rex's Plane**
  - **Size**: 80x120px
  - **Usage**: Gameplay - player aircraft
  - **Style**: Fighter plane with beagle-themed colors/details
  - **Details**: Brown/gold color scheme, beagle nose art

- **Luna's Plane**
  - **Size**: 80x120px
  - **Usage**: Gameplay - player aircraft
  - **Style**: Sleek fighter plane with dachshund theme
  - **Details**: Brown/red color scheme, dachshund silhouette

- **Paco's Plane**
  - **Size**: 80x120px
  - **Usage**: Gameplay - player aircraft
  - **Style**: Fast, agile fighter with chihuahua theme
  - **Details**: Brown/orange color scheme, chihuahua details

---

## Enemy Assets

### 2. Cat Enemy Sprites
**Purpose**: Regular enemies in gameplay

#### 2.1 Regular Cat Planes
- **Size**: 60x80px
  - **Usage**: Standard enemy aircraft
  - **Style**: Cat-themed fighter planes
  - **Variants**: 3-4 different cat breeds (Siamese, Tabby, Black Cat, etc.)
  - **Details**: Each with different color schemes and cat features

#### 2.2 Boss Cat Planes
- **Size**: 100x140px
  - **Usage**: Boss enemy aircraft
  - **Style**: Larger, more detailed cat planes
  - **Variants**: 2-3 boss designs
  - **Details**: More elaborate designs, special markings

---

## UI Assets

### 3. Interface Elements

#### 3.1 Background Images
- **Character Select Background**
  - **Size**: 1200x800px
  - **Usage**: Character selection screen background
  - **Style**: Sky/clouds theme, aviation-inspired

- **Game Background**
  - **Size**: 1200x800px
  - **Usage**: Main gameplay background
  - **Style**: Sky with clouds, parallax scrolling effect

#### 3.2 UI Elements
- **Button Frames**
  - **Size**: 200x60px (standard), 300x80px (large)
  - **Usage**: Menu buttons, selection boxes
  - **Style**: Aviation-themed frames

- **Health Bar**
  - **Size**: 200x20px
  - **Usage**: Boss health display
  - **Style**: Simple bar with frame

- **Score Display Frame**
  - **Size**: 150x40px
  - **Usage**: Score and wave counter background
  - **Style**: Aviation instrument panel style

#### 3.3 Icons
- **Bullet Icon**
  - **Size**: 16x16px
  - **Usage**: Player projectiles
  - **Style**: Simple bullet/trail effect

- **Explosion Sprites**
  - **Size**: 64x64px (4-frame animation)
  - **Usage**: Enemy destruction effects
  - **Style**: Simple explosion animation

---

## Effect Assets

### 4. Visual Effects

#### 4.1 Particle Effects
- **Engine Trail**
  - **Size**: 32x32px
  - **Usage**: Player plane engine exhaust
  - **Style**: Simple smoke/fire trail

- **Bullet Trails**
  - **Size**: 8x8px
  - **Usage**: Projectile trails
  - **Style**: Simple light trails

#### 4.2 Explosion Animations
- **Small Explosion**
  - **Size**: 48x48px (6-frame animation)
  - **Usage**: Regular enemy destruction
  - **Style**: Simple explosion sequence

- **Large Explosion**
  - **Size**: 96x96px (8-frame animation)
  - **Usage**: Boss destruction
  - **Style**: Larger explosion sequence

---

## Menu Assets

### 5. Menu Graphics

#### 5.1 Title Screen
- **Game Logo**
  - **Size**: 400x200px
  - **Usage**: Main title screen
  - **Style**: "ACES PUP" with aviation/dog theme

- **Title Background**
  - **Size**: 1200x800px
  - **Usage**: Title screen background
  - **Style**: Dramatic sky scene

#### 5.2 Menu Elements
- **Menu Button (Normal)**
  - **Size**: 200x60px
  - **Usage**: Menu navigation
  - **Style**: Aviation-themed button

- **Menu Button (Hover)**
  - **Size**: 200x60px
  - **Usage**: Menu navigation (hover state)
  - **Style**: Highlighted version of normal button

- **Menu Button (Pressed)**
  - **Size**: 200x60px
  - **Usage**: Menu navigation (pressed state)
  - **Style**: Depressed version of normal button

---

## Priority List

### High Priority (Core Gameplay)
1. **Dog Plane Sprites** (3 variants) - Essential for gameplay
2. **Cat Enemy Sprites** (3-4 variants) - Essential for gameplay
3. **Boss Cat Sprites** (2-3 variants) - Essential for boss battles
4. **Basic UI Elements** - Essential for interface

### Medium Priority (Enhanced Experience)
1. **Character Select Portraits** - Improves character selection
2. **Background Images** - Improves visual appeal
3. **Explosion Animations** - Improves feedback
4. **Particle Effects** - Improves visual polish

### Low Priority (Polish)
1. **Menu Graphics** - Can use placeholder initially
2. **Advanced Effects** - Can be added later
3. **Additional Variants** - Can expand later

---

## Technical Notes

### File Naming Convention
- Use descriptive names: `rex_plane.png`, `cat_enemy_tabby.png`
- Include size in filename if multiple sizes: `button_large.png`, `button_small.png`
- Use underscores for spaces: `boss_cat_siamese.png`

### Organization
```
assets/
├── characters/
│   ├── dogs/
│   └── cats/
├── ui/
├── effects/
├── backgrounds/
└── menus/
```

### Optimization
- Keep file sizes reasonable (under 100KB for most sprites)
- Use transparency where appropriate
- Consider sprite sheets for animations
- Test on target hardware for performance 