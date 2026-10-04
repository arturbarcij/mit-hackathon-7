Two bugs on the capture screen. Fix only these; do not touch src/content/*.json, public/model or public/audio.

1. Every test photo is rejected with "move closer". The mock checkQuality returns reason 'too_small' when the shorter side of the image is under 240 px. Our model's training images are 128 x 128 crops and the model resizes every input to 224 x 224, so 240 rejects the very images it was trained on. Change the minimum shorter side to 96 px. Keep the blur and brightness fields as they are. Keep the CONTRACTS signature: checkQuality(img: ImageBitmap): QualityResult.

2. The photo preview looks pixelated. The preview <img> uses `aspect-[4/3] w-full object-cover`, which stretches small images to full width and crops them. Change it to show the whole photo at no more than its natural size: `mx-auto block h-auto max-h-[60vh] w-auto max-w-full object-contain rounded-md border-2 border-foreground`. Keep the object URL of the original file (do not redraw it through a canvas or compress it). The summary thumbnails can stay as they are.

Then republish and tell me the URL.
