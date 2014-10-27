Slug: math-test-2-md
Date: 2014-02-14 12:13
Title: math test 2 (md)
Latex:


Latex Examples
--------------
###Inline
Latex between `$`..`$`, for example, $x^2$, will be rendered inline 
with respect to the current html block.

###Displayed Math
Latex between `$$`..`$$`, for example, $$x^2$$, will be rendered centered in
a new paragraph.

###Equations

Latex between `\begin` and `\end`, for example, \begin{equation} x^2
\end{equation}, will be rendered centered in a new paragraph with a right
justified equation number at the top of the paragraph. This equation number
can be referenced in the document. To do this, use a `label` inside of the
equation format and then refer to that label using `ref`. For example:
\begin{equation} \label{eq} X^2 \end{equation}. Now refer to that equation
number by $\ref{eq}$.

\begin{equation}
x+y+z
\end{equation}

You can also delimit multiline paragraphs of math with `$$`. In all cases, use a single `\` to call out TeX/LaTex/MathJax commands.

$$
x_0 + y
$$

## Other experiments


This is $x^2$ inline.

http://www.onemathematicalcat.org/MathJaxDocumentation/TeXSyntax.htm has some
good mathjax examples.

The bigger equation $$x^2+x-1$$ will go into its own paragraph.

Adding `TeX: {extensions: ['mhchem.js']}` to plugins/latex/latex.py enables
this: $\ce{C6H5-CH0}$

$writecap = K1 = x$

$y = g^x$

$signkey = x*y = x*H(g^x) = K1*H(g^{K1})$

$K2 = g^x = g^{K1}$

$K3 = g^{x*y} = g^{x*H(g^x)} = ({g^x})^{H(g^x)} = {K2}^{H(K2)}$

$verifykey = K3 = g^{signkey}$

\begin{equation}
x^2 - x + 1
\end{equation}

\begin{equation}
\bbox[#fcc,border:1px solid blue]{z * x_0 + y}
\end{equation}

$$
\eqalign{
K3 &= g^{x*y} \\cr
&= g^{x*H(g^x)} \\cr
&= ({g^x})^{H(g^x)} \\cr
&= {K2}^{H(K2)}
}
$$

$$
\underbrace{x + \cdots + x}_{n\rm\ times}^{\text{(note here)}}
\sqrt{x+y}
\scr{A}
\frak{B}
\cal{C}
\Bbb{D}
\infty * \frac {a+1} {b-1}
$$



Template And Article Examples
-----------------------------
To see an example of this plugin in action, look at 
[this article](http://doctrina.org/How-RSA-Works-With-Examples.html). To see how 
this plugin works with a template, look at 
[this template](https://github.com/barrysteyn/pelican_theme-personal_blog).
