# Dataset Strategy

## Layout

```
data/products/<category>/<product_name>.jpg
```

e.g.

```
data/products/sneakers/nike_air_max_97.jpg
data/products/cameras/sony_a6000.jpg
data/products/vintage_tshirts/pearl_jam_1996.jpg
```

Categories suggested by the brief: sneakers, vintage t-shirts, cameras, gaming
controllers, headphones, watches, jackets, bags. Use publicly available
images where licensing permits (manufacturer product pages, Wikimedia
Commons, your own photographed items).

## Domain A vs Domain B (the core research experiment)

For the domain-gap experiment (`ml/evaluation/domain_gap.py`, roadmap Phase
10), organize a **second, parallel** directory:

```
data/domain_gap/
├── domain_a_clean/<category>/<product>.jpg      # clean product photos
└── domain_b_cluttered/<category>/<product>_thrift.jpg  # same products,
                                                          # photographed messily
```

Each item in `domain_b_cluttered` should correspond to the *same physical
product* as one image in `domain_a_clean` (or in `data/products`, which acts
as the retrieval catalog), photographed under realistic thrift-store
conditions: cluttered background, imperfect lighting, an angle, partial
occlusion. This pairing is what lets `domain_gap.py` measure retrieval
accuracy degradation directly (Clean→Clean vs Cluttered→Clean), rather than
just reporting two unrelated numbers.

**This directory is intentionally left empty in this scaffold** — populating
it requires real photography (a phone and 30-60 minutes photographing items
around your home/room in both clean and "thrift shelf" staging is enough for
a meaningful student-project-scale experiment; 15-30 products x 2 domains is
plenty to show the effect).
