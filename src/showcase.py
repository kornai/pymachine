from machine import Machine
from monoid import Monoid

# a sa1rga printnevu3 ge1p
sarga = Machine(Monoid("sa1rga"))
# sarga.control == None, me1g nincs szo1faj
# sarga.base == Monoid("sarga"), az a pe1lda1ny

# ke1k ge1p ugyani1gy
kek = Machine(Monoid("ke1k"))

kocka = Machine(Monoid("kocka"))
# a 0. parti1cio1 a printname, kell egy elso3 parti1cio1
kocka.base.partitions.append([])
kocka.base.partitions[1].append(sarga)
# legyen egy szofaja is, ez most string, ke1so3bb FSx
kocka.control = "NOUN<ACC>"

gomb = Machine(Monoid("go2mb"))
gomb.base.partitions.append([])
gomb.base.partitions[1].append(kek)
gomb.control = "NOUN<SUBL>"

on = Machine(Monoid("ON"))
on.base.partitions.append([])
on.base.partitions.append([])
on.base.partitions[1].append(kocka)
on.base.partitions[2].append(gomb)

on = Machine(Monoid("CAUSE/AFTER"))
on.base.partitions.append([])
on.base.partitions.append([])
on.base.partitions[1].append(None) # NOM
on.base.partitions[2].append(on)

