
#import "@preview/hydra:0.6.1": hydra

#let fantasy-encyclopedia(title:"", body) = {

  set page(paper: "a4", numbering: none, background:{image("cover.png", width: 100%)})

  align(horizon+center,text(title, font: "Libertinus Serif", size: 40pt, fill: rgb("#cdb15b")))
  pagebreak()


  set page(
    paper: "a4",
    header: context {
            if calc.odd(here().page()) {
              align(right, emph(hydra(1,skip-starting: false,use-last: true)))
            } else {
              align(left, emph(hydra(1,skip-starting: false))) 
            }
            line(length: 100%)
          },
    footer: context { 
            if calc.odd(here().page()) {
              align(right, counter(page).display("1"))
            } else {
              align(left, counter(page).display("1")) 
            }            
          },      
    columns: 2,
    numbering: "1",
    background: context{
            if calc.odd(here().page()) {
              scale(x: -100%,image("page_border.png", width: 100%))
            } else {
              image("page_border.png", width: 100%)
            }
      
    }
  )
  counter(page).update(1)

  


  set par(justify: true)
  set text(
    font: "Libertinus Serif",
    size: 11pt,
  )
  set align(left)
  body
}