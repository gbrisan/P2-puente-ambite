# P2-puente-ambite

Este repositorio está compuesto por un total de 4 documentos

Un documento pdf en el que se desarrollan las ideas previas para la construcción de un programa que regule el tránsito de vehículos y peatones en un puente de una única dirección. Se tiene en cuenta que los coches pueden venir en dirección norte y sur y que por seguridad no pueden cruzar el puente coches y peatones a la vez.

Posteriormente, las ideas plasmadas se convierten en un programa del que se presentan 3 versiones. En cada una de ellas se van revisando los problemas principales en los problemas concurrentes y se van modificando los errores hasta obtener la versión final.

En la versión final podemos ver un programa concurrente controlado por un monitor que se encarga de controlar el tráfico del puente. 
Para conseguirlo se diseña una clase con todas las variables necesarias y una serie de funciones que se encargan de controlar si hay o no peatones o coches en el puente, en qué dirección y cuándo debe entrar cada uno de ellos en el puente para asegurar la seguridad.

Además, se establece una entrada por turnos que nos garantiza la ausencia de inanición y la justicia. Estos turnos se establecen de forma que ninguno de los elementos que pueden entrar en el puente, coches del norte, coches del sur o peatones, puedan aliarse entre ellos para no dejar paso al otro.
