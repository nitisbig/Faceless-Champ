[calm] Your calculator has a secret. [pause] Deep inside, it can only do a few simple things. Add. Subtract. Multiply. Divide. That's it.

So what happens when you ask it for the sine of zero point five? There is no tiny circle hidden in the chip. No little triangle being measured. And yet, in a blink, it answers. Zero point four seven nine four.

[curious] How does a machine that can only add and multiply know anything about waves?

The answer is one of the most beautiful tricks in all of mathematics. [pause] It says that almost any smooth curve, a wave, a growth curve, a slow decay, can be rebuilt out of the simplest pieces we know. A constant. A straight line. A parabola. A cubic. Stacked one on top of another, until the copy hugs the original so tightly you cannot tell them apart.

In this video, we will watch a polynomial slowly wrap itself around a sine wave. We will see why strange numbers called factorials show up, uninvited, in every formula. We will compute the famous number e by hand, using nothing but fractions. [pause] And then we will meet a perfectly smooth, innocent looking curve where the trick suddenly fails, for a reason hiding in a place you cannot even see on the graph.

This is the Taylor series. [pause] Let's build it from scratch.

Start with what a computer finds easy. Take a number x. Multiply it by itself. Multiply by a constant. Add a few of those together. Three x squared, minus two x, plus five. That is a polynomial. Every piece of it is just multiplying and adding. Give a computer any x, and it can evaluate this instantly.

Polynomials are friendly in other ways too. Their slopes are easy to find. The areas under them are easy to find. They never jump, never break, never surprise you.

Sine, on the other hand, is defined by a circle. The exponential function is defined by growth. The logarithm, by an area under a curve. Beautiful ideas. [pause] But you cannot type a circle into a chip.

So here is the plan. If we cannot compute the real function, let's build a polynomial that pretends to be it. A perfect impostor. [pause] The only question is how to make the disguise convincing.

Let's try it with the cosine curve, right around the point x equals zero. Cosine starts at the top of a hill, at a height of one, and gently curves down on both sides.

First attempt. The simplest polynomial there is, a constant. Just match the height. Cosine of zero is one, so our impostor is the flat line, y equals one. [pause] Right at zero, it's perfect. But move a little to the side, and the real curve falls away, while our line stays stubbornly flat.

What did we miss? The slope. So let's match that too. At the top of the hill, cosine is perfectly level. Its slope is zero. Our flat line also has a slope of zero. So nothing changes yet.

What is still missing is the bend. Cosine is curving downward. And to capture a bend, we need a parabola. An x squared term.

Now here is a subtle point. The bend of a curve is measured by its second derivative, the slope of the slope. For cosine at zero, that bend is minus one. So how much x squared do we need?

Take x squared and find its slope. Two x. Take the slope again. Two. [pause] So x squared has a bend of two, not one. To get a bend of exactly minus one, we need minus one half of x squared.

Our new impostor is one, minus x squared over two. [pause] Look at it on the graph. Near zero, it bends down exactly like the cosine. A much better disguise.

Keep going. The third derivative of cosine at zero is zero, so we skip it. The fourth derivative is plus one. To match it, we need an x to the fourth term. But x to the fourth, differentiated four times, becomes four times three times two times one. Twenty four. So we divide by twenty four.

One, minus x squared over two, plus x to the fourth over twenty four.

[thoughtful] Two. Twenty four. Notice the pattern. Two is two times one. Twenty four is four times three times two times one. These are factorials. Four factorial means four multiplied by every whole number below it.

And they show up for a simple reason. Every time you take the derivative of a power, the exponent drops down in front and multiplies. Take enough derivatives, and you have multiplied all of those exponents together. Dividing by the factorial cancels that out, so each term delivers exactly the amount we asked for.

Now we can write the whole trick as a single recipe.

To copy a function near zero, find its value, its first derivative, its second derivative, its third, and so on, all measured at zero. Then the copy is: the value, plus the first derivative times x, plus the second derivative times x squared over two factorial, plus the third derivative times x cubed over three factorial, and on and on, forever.

[pause] Each term has one job. The x term handles the slope. The x squared term handles the bend. The x cubed term handles how the bend is changing. And here is the clever part. At zero, each new term is completely invisible to all the lower derivatives. So adding it never spoils the features you have already matched. You can stack term after term, and each one only brings new information.

That infinite sum is called the Taylor series. When we stop after a few terms, we call it a Taylor polynomial. And with every term you add, the copy hugs the original a little further out.

Zero isn't special, by the way. You can center the copy at any point you like, simply by measuring distances from that point instead. The idea stays exactly the same.

Let's put the recipe to work on the most famous function of all. E to the x.

This function has one remarkable property. Its slope is always equal to its own height. So its derivative is itself. Its second derivative is itself. Every derivative is itself. And at zero, e to the zero is one. So every single derivative at zero is simply one.

Feed that into the recipe, and the series comes out wonderfully clean. One, plus x, plus x squared over two factorial, plus x cubed over three factorial, plus x to the fourth over four factorial, and so on.

Now set x equal to one, and out comes the number e itself.

[calm] One. [pause] Plus one. That's two. [pause] Plus one half. Two point five. [pause] Plus one sixth. Two point six six seven. [pause] Plus one over twenty four. Two point seven zero eight. [pause] Plus one over one hundred twenty. Two point seven one six seven.

The true value of e is two point seven one eight two eight. After just six terms, we are already very close. After ten terms, the first seven decimal places are correct.

Why so fast? Because factorials grow ridiculously quickly. Ten factorial is already more than three and a half million. The terms shrink so fast that the sum settles down almost immediately.

Now let's return to the question from the very beginning. How does your calculator find the sine of zero point five?

Apply the recipe to sine at zero. The derivatives of sine go around in a loop. Sine, then cosine, then minus sine, then minus cosine, and back to sine again. At zero, these give zero, one, zero, minus one, over and over.

So all the even powers vanish, and the signs take turns. Sine of x equals x, minus x cubed over six, plus x to the fifth over one hundred twenty, minus x to the seventh over five thousand forty, and on forever.

Let's watch it on the graph. [calm] The first term, just x, is a straight line through the center. It hugs the sine wave for a short stretch, then shoots away. Add the cubic term, and the line bends back down, following the first hump. Add the fifth power, and it reaches further, catching the valley. With every new term, the polynomial wraps itself one step further along the wave, like a vine climbing a fence.

Now the calculation. x is zero point five. The first term is zero point five. The second term is zero point one two five divided by six, about zero point zero two zero eight. Subtract it, and we get zero point four seven nine two. The third term adds a tiny zero point zero zero zero two six.

The total is zero point four seven nine four two seven. [pause] The true answer is zero point four seven nine four two five. Three terms. A few multiplications and additions. And we are correct to five decimal places.

[softly] That is the secret your calculator was keeping. Real chips use clever refinements of this idea, but polynomials like this one sit at the heart of it. The machine does not know what a circle is. It only knows the polynomial that pretends to be one.

And look at that very first term. For small angles, the sine of x is almost exactly x. Physicists use this all the time. It is how the swing of a pendulum becomes a simple equation you can solve by hand.

So far, the series has worked everywhere we looked. For e to the x, for sine, and for cosine, you can travel as far from zero as you like. Add enough terms, and the copy always catches up.

[pause] But not every function is so kind.

Look at this curve. One divided by one plus x squared. It is a gentle hill, highest at zero, sliding smoothly down on both sides. No breaks. No corners. No sudden jumps. As innocent as a curve can be.

Its Taylor series is simple too. One, minus x squared, plus x to the fourth, minus x to the sixth, and so on.

Try x equals zero point five. The terms shrink, and the sum settles on zero point eight. Exactly right.

Now try x equals one. One, minus one, plus one, minus one. [pause] The sum never settles. It just flips back and forth forever. And beyond one, it gets even worse. The terms grow larger and larger, and the polynomial flies off toward infinity, while the real curve sits there, perfectly calm.

[curious] Why? The graph shows nothing strange at x equals one. Nothing at all.

The reason lives off the graph, in the complex numbers. Suppose x is allowed to be imaginary. At x equals i, the square root of minus one, x squared becomes minus one, and the bottom of the fraction becomes zero. The function explodes. [pause] And that hidden explosion sits at a distance of exactly one from zero.

Here is the rule. A Taylor series works inside a circle around its center. That circle grows only until it touches the nearest trouble spot, even a trouble spot hiding in the complex plane. For this curve, the circle has a radius of one. On the ordinary number line, that means the series can only be trusted between minus one and one.

This distance is called the radius of convergence. [thoughtful] It is a reminder that our polynomial impostor only knows what the function looks like near a single point. How far that knowledge reaches depends on secrets the graph does not show.

Once you know this trick, you start seeing it everywhere.

Engineers keep the first few terms to turn hard equations into easy ones. Game engines use short polynomials to compute waves and rotations quickly. Optimization methods in machine learning replace a complicated surface with a simple bowl, which is just a Taylor series stopped at the squared term.

And one of the most famous examples comes from Einstein. In relativity, the energy of a moving object is its mass times c squared, divided by the square root of one minus v squared over c squared. That looks nothing like the physics we learn in school. [pause] But expand it as a Taylor series in the speed, and the first two terms are m c squared, plus one half m v squared.

The first term is the energy locked inside mass itself. The second is the familiar kinetic energy from school physics. [pause] Newton's formula was never wrong. It was simply the first useful term of a deeper series.

[calm] So let's look back at what we built.

Computers can only add and multiply, so polynomials are the functions they truly understand.

To copy any smooth function near a point, match its value, then its slope, then its bend, then each higher derivative, one term at a time.

Each term is a derivative divided by a factorial, because the factorial cancels what repeated differentiation multiplies in.

With this one recipe, the number e becomes a sum of simple fractions, and sine becomes a handful of multiplications your calculator can do in a blink.

And every series has a reach. It works inside a circle that stops at the nearest trouble spot, even one hidden in the complex numbers.

[pause] Here is something to think about until next time. What happens if you put an imaginary number into the series for e to the x? [pause] Sort the terms carefully, and the series for cosine and sine fall out, side by side. Growth, waves, and circles, all part of one family.

[softly] Any function. Built from the simplest pieces. One term at a time.
