
#import "@preview/hydra:0.6.1": hydra

#let fantasy-encyclopedia(title:"", body) = {
  set page(
    paper: "a4",
    header: context {
  //if calc.odd(here().page()) {
    align(left, emph(hydra(1)))
    //align(right, emph(hydra(1)))
  //} else {
  //  align(left, emph(hydra(2)))
  //}
  //line(length: 100%)
},
    columns: 2,

  )
  set par(justify: true)
  set text(
    font: "Libertinus Serif",
    size: 11pt,
  )
  set align(left)
  body
}