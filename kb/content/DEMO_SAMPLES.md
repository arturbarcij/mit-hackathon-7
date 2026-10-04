# Demo samples: "Try with sample leaves"

Owner: content-voice. Built by `kb/content/demo_samples_build.py` from `kb/research/wild_set.csv`. Files: `app/public/demo/*.jpg` and `app/public/demo/manifest.json`.

These are real photos from public sources in Central and South America, Hawaii and elsewhere. None is from Kenya or from Noor's farm. Labels are source hints, not verified by an agronomist. They are not synthetic, but the demo story built on them (Noor's 10-leaf check) is a simulation and must be labelled "simulated" on screen.

## How the app uses them

- Load `/demo/manifest.json`. Use `local_path` first (served by the app, works offline once cached). `image_url` is the public fallback. `image_url_full` is the full-size original.
- Samples 01 to 10 are the 10-leaf check: 6 rust, 3 healthy, 1 other problem. Expected result: rust likely, refer to the officer.
- Sample 11 (berries) must get the "I cannot judge berries" answer. Sample 12 (dark, cluttered) must get the retake prompt.
- Show the attribution line under each photo, and a link to `page_url` and `licence_url`. CC BY-SA photos stay under CC BY-SA.

## Table

| File | Role | Source hint | Our visual note | Author | Licence | Page |
|---|---|---|---|---|---|---|
| sample01_rust.jpg | rust | rust (identified as Hemileia vastatrix) | One leaf on an open palm, underside. Many orange powdery pustules and a few brown dead patches. Daylight, sharp. | Emily Franzen | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | [link](https://www.inaturalist.org/observations/146581237) |
| sample02_rust.jpg | rust | rust (identified as Hemileia vastatrix) | Close-up of a leaf underside. Two round orange powdery lesions, one with a dark centre; one small hole. Sharp. | B. Phalan | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | [link](https://www.inaturalist.org/observations/303784616) |
| sample03_rust.jpg | rust | rust | Leaf held between fingers, underside. Large orange powdery patches along the leaf. Daylight. | Smartse | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) | [link](https://commons.wikimedia.org/wiki/File:Hemileia_vastatrix_-_coffee_leaf_rust.jpg) |
| sample04_rust.jpg | rust | rust (identified as Hemileia vastatrix) | Leaf held by hand, upper side. Round yellow spots with orange centres. Daylight, sharp. | Mark Richman | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | [link](https://www.inaturalist.org/observations/146509854) |
| sample05_rust.jpg | rust | rust (identified as Hemileia vastatrix) | Leaf held in fingers, underside. Many small orange spots and some brown edges. Slightly soft focus. | Eric Schmidt | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | [link](https://www.inaturalist.org/observations/303166434) |
| sample06_rust.jpg | rust | rust (identified as Hemileia vastatrix) | Upper side of one leaf on the plant. Many small pale yellow spots and one hole; no orange powder visible from this side (early or upper-side view). | Juanito Escamilla | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | [link](https://www.inaturalist.org/observations/64993202) |
| sample07_healthy.jpg | healthy | coffee_leaf_unverified | Several glossy dark green leaves on the plant. No spots visible. Not a single detached leaf. | Agnieszka Kwiecień, Nova | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | [link](https://commons.wikimedia.org/wiki/File:Coffea_arabica_Kawa_arabska_2021-0-09_02.jpg) |
| sample08_healthy.jpg | healthy | coffee_leaf_unverified | Glossy leaves on the plant with one bright young leaf in front. No spots visible. | Agnieszka Kwiecień, Nova | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | [link](https://commons.wikimedia.org/wiki/File:Coffea_arabica_Kawa_arabska_2021-0-09_01.jpg) |
| sample09_healthy.jpg | healthy | coffee_leaf_unverified | One detached leaf on a dark cloth (close to our capture protocol). Mostly clean; faint brown marks on the left half, so it may score borderline. | Monalperoth | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | [link](https://commons.wikimedia.org/wiki/File:Coffea_arabica_coffee_tuvvur.JPG) |
| sample10_other.jpg | other_problem | coffee_leaf_unverified | Leaf underside held in a gloved hand. Dry brown edges all round, no orange powder. Not rust; the source gives no cause (could be scorch, drought or nutrients). App should say: ask the officer. | Forest and Kim Starr | [CC BY 3.0 us](https://creativecommons.org/licenses/by/3.0/us/) | [link](https://commons.wikimedia.org/wiki/File:Starr-120229-3124-Coffea_arabica-leaf_underside-Waikapu_Valley-Maui_(25136592695).jpg) |
| sample11_berry.jpg | edge_case_berry | coffee_leaf_unverified | Cluster of ripe red coffee cherries with two leaves. Out of scope: the app must say it cannot judge berries. | Forest and Kim Starr | [CC BY 3.0 us](https://creativecommons.org/licenses/by/3.0/us/) | [link](https://commons.wikimedia.org/wiki/File:Starr-120120-1777-Coffea_arabica-fruit_and_leaves-Enchanting_Floral_Gardens_of_Kula-Maui_(25132562715).jpg) |
| sample12_poor.jpg | edge_case_poor_photo | coffee_leaf_unverified | Many glossy leaves in deep shade. Dark, cluttered, no single leaf fills the frame. Should trigger the retake prompt. | David J. Stang | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | [link](https://commons.wikimedia.org/wiki/File:Coffea_arabica_42zz.jpg) |

## Attribution text the app must show

Short line under each photo: `Photo: <author>, <source>, <licence>.` with links to the page and the licence. Full list for the About or Sources page:

- sample01_rust.jpg: photo by Emily Franzen, iNaturalist (https://www.inaturalist.org/observations/146581237), CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Resized to 640 px.
- sample02_rust.jpg: photo by B. Phalan, iNaturalist (https://www.inaturalist.org/observations/303784616), CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Resized to 640 px.
- sample03_rust.jpg: photo by Smartse, Wikimedia Commons (https://commons.wikimedia.org/wiki/File:Hemileia_vastatrix_-_coffee_leaf_rust.jpg), CC BY-SA 3.0 (https://creativecommons.org/licenses/by-sa/3.0/). Resized to 640 px.
- sample04_rust.jpg: photo by Mark Richman, iNaturalist (https://www.inaturalist.org/observations/146509854), CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Resized to 640 px.
- sample05_rust.jpg: photo by Eric Schmidt, iNaturalist (https://www.inaturalist.org/observations/303166434), CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Resized to 640 px.
- sample06_rust.jpg: photo by Juanito Escamilla, iNaturalist (https://www.inaturalist.org/observations/64993202), CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Resized to 640 px.
- sample07_healthy.jpg: photo by Agnieszka Kwiecień, Nova, Wikimedia Commons (https://commons.wikimedia.org/wiki/File:Coffea_arabica_Kawa_arabska_2021-0-09_02.jpg), CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/). Resized to 640 px.
- sample08_healthy.jpg: photo by Agnieszka Kwiecień, Nova, Wikimedia Commons (https://commons.wikimedia.org/wiki/File:Coffea_arabica_Kawa_arabska_2021-0-09_01.jpg), CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/). Resized to 640 px.
- sample09_healthy.jpg: photo by Monalperoth, Wikimedia Commons (https://commons.wikimedia.org/wiki/File:Coffea_arabica_coffee_tuvvur.JPG), CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/). Resized to 640 px.
- sample10_other.jpg: photo by Forest and Kim Starr, Wikimedia Commons (https://commons.wikimedia.org/wiki/File:Starr-120229-3124-Coffea_arabica-leaf_underside-Waikapu_Valley-Maui_(25136592695).jpg), CC BY 3.0 us (https://creativecommons.org/licenses/by/3.0/us/). Resized to 640 px.
- sample11_berry.jpg: photo by Forest and Kim Starr, Wikimedia Commons (https://commons.wikimedia.org/wiki/File:Starr-120120-1777-Coffea_arabica-fruit_and_leaves-Enchanting_Floral_Gardens_of_Kula-Maui_(25132562715).jpg), CC BY 3.0 us (https://creativecommons.org/licenses/by/3.0/us/). Resized to 640 px.
- sample12_poor.jpg: photo by David J. Stang, Wikimedia Commons (https://commons.wikimedia.org/wiki/File:Coffea_arabica_42zz.jpg), CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/). Resized to 640 px.

Footer text: "Sample photos come from iNaturalist and Wikimedia Commons under Creative Commons licences. They are not from Kenya. Labels are hints from the source, not checked by an agronomist."

## Open points

- Public URLs were built from the documented patterns and not fetched (no internet from the build machines). Check one iNaturalist and one Wikimedia link in a browser before the video.
- iNaturalist `medium` images are about 500 px on the long side; Wikimedia `?width=640` returns a redirect to a 640 px thumbnail.
- No leaf miner or brown eye spot photo with an open licence was found in the wild set. Row 44 (CC0, hint rust) has round brown lesions with a pale ring that look closer to brown eye spot to a non-expert; not used, ask the officer before relabelling.
- No truly blurry leaf photo with an open licence exists in the set; sample 12 is dark and cluttered instead.
- Sample 09 has faint brown marks and may score borderline.
