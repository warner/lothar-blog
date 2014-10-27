:slug: math-test-rst
:title: math test
:date: 2014-02-14 12:12
:latex:

This is $x^2$ inline.

http://www.onemathematicalcat.org/MathJaxDocumentation/TeXSyntax.htm has some
good mathjax examples.

The bigger equation $$x^2+x-1$$ will go into its own paragraph.

$$
\\bbox[#fcc,border:1px solid blue]{z * x_0 + y}
$$

Adding `TeX: {extensions: ['mhchem.js']}` to plugins/latex/latex.py enables
this:

$$
\\ce{C6H5-CH0}
$$

$$
\\begin{equation}
x^2 - x + 1
\\end{equation}
$$

$writecap = K1 = x$

$y = g^x$

$signkey = x*y = x*H(g^x) = K1*H(g^{K1})$

$K2 = g^x = g^{K1}$

$K3 = g^{x*y} = g^{x*H(g^x)} = ({g^x})^{H(g^x)} = {K2}^{H(K2)}$

$verifykey = K3 = g^{signkey}$

$$
\\eqalign{
K3 &= g^{x*y} \\cr
&= g^{x*H(g^x)} \\cr
&= ({g^x})^{H(g^x)} \\cr
&= {K2}^{H(K2)}
}
$$

$$
\\underbrace{x + \\cdots + x}_{n\\rm\\ times}^{\\text{(note here)}}
\\sqrt{x+y}
\\scr{A}
\\frak{B}
\\cal{C}
\\Bbb{D}
\\infty * \\frac {a+1} {b-1}
$$
