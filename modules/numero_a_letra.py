#! /usr/bin/env python
# -*- coding: utf-8 -*-

""" Expresa números naturales y el cero en letras (actualmente hasta 999 billones.)"""


""" Copyright 2010 Alan Etkin, hexa662@gmail.com.
    
Este programa se distribuye bajo los términos de la licencia GPL.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, version 3 of the License, or any later
version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""


ceroalveintederecha = ["cero","uno","dos","tres","cuatro","cinco","seis","siete","ocho","nueve","diez", \
         "once","doce","trece","catorce","quince","dieciseis","diecisiete","dieciocho","diecinueve","veinte", \
         "veintiuno", "veintidós", "veintitrés", "veinticuatro", "veinticinco", "veintiseis", "veintisiete", \
         "veintiocho", "veintinueve"]

decenas = [None, "diez", "veinte", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa"]
centenasderecha = [None, "cien", "docientos", "trecientos", "cuatrocientos", "quinientos", "seiscientos", "setecientos", "ochocientos", "novecientos"]
centenasizquierda = [None, "ciento", "docientos", "trecientos", "cuatrocientos", "quinientos", "seiscientos", "setecientos", "ochocientos", "novecientos"]
ceroalveinteizquierda = ["cero","un","dos","tres","cuatro","cinco","seis","siete","ocho","nueve","diez", \
         "once","doce","trece","catorce","quince","dieciseis","diecisiete","dieciocho","diecinueve","veinte", \
         "veintiún", "veintidós", "veintitrés", "veinticuatro", "veinticinco", "veintiseis", "veintisiete", \
         "veintiocho", "veintinueve"]


def convertir(numero):
    """ Pasa un valor entero entre 0 y 999 billones a letras

    """

    if (0 > numero) or (numero >= 1000000000000000):
        raise ValueError("El número ingresado está fuera del rango esperado.")

    ceromiles = False
    ceromillones= False
    ceromilesdemillones = False
    cerobillones = False

    singmiles = False
    singmillones = False
    singmilesdemillones = False
    singbillones = False

    strnumero = str(numero)
    strunidades = ""
    strmiles = ""
    strmillones = ""
    strmilesdemillones = ""
    strbillones = ""
    texto = ""

    if 0 < len(strnumero) < 4:
        texto = numero_a_letra(numero, True)

    elif 3 < len(strnumero) < 7:
        unidades = numero_a_letra(int(str(numero)[len(strnumero) -3:]), True)

        strnumero = strnumero[:len(strnumero) -3]

        miles = numero_a_letra(int(strnumero), False)

        if miles == "un":
            texto = "mil " + unidades
        else:
            texto = miles + " mil " + unidades

    elif 6 < len(strnumero) < 10:
        strunidades = strnumero[len(strnumero) -3:]

        strmiles = strnumero[len(strnumero) -6: len(strnumero) -3]
        if int(strmiles) == 0:
            ceromiles = True
        elif int(strmiles) == 1:
            singmiles = True

        strmillones = strnumero[: len(strnumero) -6]
        if int(strmillones) == 1:
            singmillones = True
            
        unidades = numero_a_letra(int(strunidades), True)

        miles = numero_a_letra(int(strmiles), False)

        millones = numero_a_letra(int(strmillones), False)


        if singmillones:
            texto += "un millón "
        else:
            texto += millones + " millones "

        if (not ceromiles):
            if singmiles:
                texto += " mil "
            else:
                texto += miles + " mil "
        else:
            pass

        texto += unidades

    elif 9 < len(strnumero) < 13:
        strunidades = strnumero[len(strnumero) -3:]

        strmiles = strnumero[len(strnumero) -6: len(strnumero) -3]
        if int(strmiles) == 0:
            ceromiles = True
        elif int(strmiles) == 1:
            singmiles = True

        strmillones = strnumero[len(strnumero) -9: len(strnumero) -6]
        if int(strmillones) == 0:
            ceromillones = True
        elif int(strmillones) == 1:
            singmillones = True

        strmilesdemillones = strnumero[: len(strnumero) -9]
        if int(strmilesdemillones) == 1:
            singmilesdemillones = True
            
        unidades = numero_a_letra(int(strunidades), True)

        miles = numero_a_letra(int(strmiles), False)

        millones = numero_a_letra(int(strmillones), False)

        milesdemillones = numero_a_letra(int(strmilesdemillones), False)

        if singmilesdemillones:
            if ceromillones:
                texto += "mil millones "
            else:
                texto += "mil "
        else:
            if ceromillones:
                texto += milesdemillones + " mil millones "
            else:
                texto += milesdemillones + " mil "

        if (not ceromillones):
            if singmillones:
                texto += " un millón "
            else:
                texto += millones + " millones "
        else:
            pass

        if (not ceromiles):
            if singmiles:
                texto += " mil "
            else:
                texto += miles + " mil "
        else:
            pass


        texto += unidades


    elif 12 < len(strnumero) < 16:
        strunidades = strnumero[len(strnumero) -3:]

        strmiles = strnumero[len(strnumero) -6: len(strnumero) -3]
        if int(strmiles) == 0:
            ceromiles = True
        elif int(strmiles) == 1:
            singmiles = True

        strmillones = strnumero[len(strnumero) -9: len(strnumero) -6]
        if int(strmillones) == 0:
            ceromillones = True
        elif int(strmillones) == 1:
            singmillones = True

        strmilesdemillones = strnumero[len(strnumero) -12: len(strnumero) -9]
        if int(strmilesdemillones) == 0:
            ceromilesdemillones = True
        elif int(strmilesdemillones) == 1:
            singmilesdemillones = True

        strbillones = strnumero[: len(strnumero) -12]
        if int(strbillones) == 1:
            singbillones = True
        elif int(strbillones) == 0:
            cerobillones = True

        unidades = numero_a_letra(int(strunidades), True)

        miles = numero_a_letra(int(strmiles), False)

        millones = numero_a_letra(int(strmillones), False)

        milesdemillones = numero_a_letra(int(strmilesdemillones), False)

        billones = numero_a_letra(int(strbillones), False)

        if singbillones:
            texto += "un billón "

        else:
            texto += billones + " billones "

        if (not ceromilesdemillones):
            if singmilesdemillones:
                if ceromillones:
                    texto += "mil millones "
                else:
                    texto += milesdemillones + " mil "
            else:
                if ceromillones:
                    texto += milesdemillones + " mil millones "
                else:
                    texto += milesdemillones + " mil "
                    
        else:
            if ceromillones:
                pass
            
            else:
                pass

        if (not ceromillones):
            if singmillones:
                texto += " un millón "
            else:
                texto += millones + " millones "
        else:
            pass

        if (not ceromiles):
            if singmiles:
                texto += " mil "
            else:
                texto += miles + " mil "
        else:
            pass


        texto += unidades


    # si termina con "cero" y el valor no es "cero" entonces sacar el "cero"
    if ((numero > 0) and (texto[len(texto) - 4:] == "cero")):
        texto = texto[:len(texto) - 4]

    return texto


def numero_a_letra(valor, final):
    """ Expresa un valor entero entre 0 y 999 en letras """
    
    oracion = ""
    valorenstr = str(valor)
    subvalor = valor

    if ((valor == 1) and (not final)):
        return "un"

    """ transforma un número de tres cifras a letras """
    if 0 < len(valorenstr) <= 2:
        if -1 < valor < 30:
            oracion = ceroalveintederecha[valor]

        else:
            if valor % 10 != 0:
                oracion = decenas[int(valorenstr[0])] + " y " + ceroalveintederecha[int(valorenstr[1])]
            else:
                oracion = decenas[int(valorenstr[0])]

    elif len(valorenstr) == 3:
        if valor % 100 == 0:
            oracion = centenasderecha[int(valorenstr[0])]
        else:
            oracion = centenasizquierda[int(valorenstr[0])]

            subvalor = int(valorenstr[1:])
            subvalorenstr = str(subvalor)
            if -1 < subvalor < 30:
                oracion += " " + ceroalveintederecha[subvalor]
            else:
                if valor % 10 != 0:
                    oracion += " " + decenas[int(subvalorenstr[0])] + " y " + ceroalveintederecha[int(subvalorenstr[1])]
                else:
                    oracion += " " + decenas[int(subvalorenstr[0])]

    if ( (not final) and (oracion[len(oracion) - 3:] == "uno") and (valor != 1)):
        oracion = oracion[: len(oracion) -3]

        if 10 < subvalor < 30:
            oracion += "ún"
        else:
            oracion += "un"

    elif ( (not final) and (valor == 1)):
        if 10 < subvalor < 30:
            oracion += "ún"
        else:
            oracion += "un"
        
    return oracion

if __name__ == "__main__":
    salir = False
    while salir != True:
        numero = raw_input("Ingrese un número a convertir: ")
        print
        print(convertir(int(numero)))
        salir = bool(raw_input("Ingrese un caracter e Intro para salir o sólo Intro para continuar: "))



