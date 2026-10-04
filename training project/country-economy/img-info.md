# Country Economy image slots

Save the six files below in this project's **image/** folder. Filenames are exact:
`1.png` through `6.png`. The normal command uses `--image auto`: existing files load
automatically, and missing files remain labeled boxes. `--image placeholder` forces
boxes even when files exist. `--image required` checks that every asset is available.
Existing corrupt files are reported as errors in auto/required mode.

Use PNG exports at the suggested size or larger. Scenes use **cover** fitting:
keep the important subject in the central 75%, leaving room for edge cropping.
Do not include text, numbers, charts, logos, flags, or captions in the images.
Library components draw all explanatory labels, charts, and arrows.

Every prompt uses this shared art direction:

> Minimal editorial illustration for an accessible finance documentary. White
> background (#FFFFFF), warm ivory surfaces (#F4F3EE), terracotta accents (#C15F3C),
> taupe details (#B1ADA1), and fine charcoal outlines (#292724). Flat geometric forms,
> restrained texture, soft paper feeling, generous empty space, clear silhouettes.
> No lettering, numerals, branding, flags, borders, charts, or watermarks. Landscape
> composition with the subject centered and safe margins for cropping.

| File | Suggested size | Scene use | Subject prompt to append |
| --- | --- | --- | --- |
| `1.png` | 1600×1020 | Opening, 0.07–13.1s | A person at a kitchen table in the morning watching a television news broadcast. An abstract government-building silhouette on the television; a mug and window with morning light. Calm setting with a subtle feeling of concern. |
| `2.png` | 1600×1000 | Household comparison and budget flow | A fictional government treasury building with columns, simple steps, and a small civic plaza. A few people approaching it. Neutral architecture with no national flag or recognizable real institution. |
| `3.png` | 1520×900 | Economic shocks | A quiet factory district and shuttered storefronts under gathering clouds, with a small damaged road in the foreground. Suggest an economic shock without depicting violence or a specific real country. |
| `4.png` | 1500×880 | Foreign-currency sources | A working export port with container cranes, a cargo ship, and stacked containers. Clear geometric forms; no company branding or numbers on containers. |
| `5.png` | 1500×860 | Import dependence | A simple editorial montage of a hospital, factory machinery, fuel storage, and food crates connected through a central cargo pallet. Organize the objects naturally without graphic arrows or written labels. |
| `6.png` | 1460×940 | Household consequences | Two ordinary people shopping for groceries at a modest market stall, considering a small basket and a few available goods. Thoughtful expressions; no written price tags or signs. |

The country is fictional except for the narration's US-dollar monetary-system
example. Images must not imply that the narrated illustrative debt figures describe
a specific real country. These prompts are ready to use; no generated images are
required for testing.
