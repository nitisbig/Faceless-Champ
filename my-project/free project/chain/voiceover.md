Right now, somewhere in the world, a neural network is learning. It has billions of tiny dials, and every single dial must be nudged in exactly the right direction, by exactly the right amount.

But how does it know which way to turn one dial, buried deep inside, many layers away from the answer it is judged on?

The answer is one idea from calculus. An idea you may have memorized, without ever feeling why it works. The chain rule.

It is the same idea that tells you how fast a shadow races across the ground when a lamp swings overhead, and how a tiny change in an interest rate ripples through a bank balance.

In the next seven minutes, we will build the chain rule from nothing. We start with a simple picture: three gears turning one another. Then we derive the rule from first principles, using only the definition of a derivative. We test it on a real example, the sine of x squared, and watch the numbers agree. And finally, we return to that neural network, and discover that its entire learning process is this one rule, repeated again and again.

By the end, you will not just know the formula. You will see it.

Imagine three gears in a row, glowing against a dark background. The first gear, call it gear A, meshes with the second, gear B. Gear B meshes with the third, gear C.

Suppose every time gear A makes one full turn, gear B makes two full turns. So gear B moves twice as fast as gear A. Label that rate on screen: times two.

Now suppose every time gear B makes one full turn, gear C makes three full turns. So gear C moves three times as fast as gear B. Label that rate: times three.

Here is the question. When gear A turns once, how many times does gear C turn?

Gear A turns once. Gear B turns twice. And each of those two turns sends gear C around three times. Two times three. Six full turns.

Watch the two and the three slide together and merge into a six. Rates multiply.

Hold on to that, because that is the chain rule in disguise. A derivative is just a rate: how fast an output changes compared to its input. And when one thing drives a second thing, which drives a third, the rates multiply.

Now let us swap the gears for functions. Picture two machines sitting side by side, connected by a pipe. A number, x, enters the first machine, which we call g. Out comes a new number, u. Then u enters the second machine, called f, and out comes the final number, y.

So y equals f of g of x. A function inside a function.

We want to know: if we nudge x by a tiny amount, how much does y move?

Watch the nudge travel. On a number line, we push x forward by a tiny step, which we call delta x. The first machine stretches or squeezes that step into a new step in u, called delta u. Then the second machine stretches or squeezes delta u into a step in y, called delta y.

Each machine behaves like a gear, with its own local rate. The first machine's rate compares delta u to delta x. The second machine's rate compares delta y to delta u. The nudge travels down the chain, getting scaled at every link.

Let us make this precise. The derivative of y with respect to x is defined as a limit: the change in y divided by the change in x, as the change in x shrinks toward zero.

Now comes one small trick. We rewrite delta y over delta x as two fractions multiplied together: delta y over delta u, times delta u over delta x.

Is that allowed? Watch the screen. Delta u sits on the top of one fraction and the bottom of the other, so it cancels, leaving exactly what we started with. Nothing has changed. We have only added a stepping stone in the middle.

Now look at each piece. The right fraction, delta u over delta x, is the rate of the first machine. The left fraction, delta y over delta u, is the rate of the second machine.

Next, let delta x shrink toward zero. Because the first machine is smooth, when delta x shrinks, delta u shrinks right along with it. So both fractions settle into true derivatives.

The left fraction becomes the derivative of y with respect to u. The right fraction becomes the derivative of u with respect to x.

And there it is. The derivative of y with respect to x equals the derivative of y with respect to u, times the derivative of u with respect to x.

In plain words: the rate of the outer machine, measured at the inner machine's output, times the rate of the inner machine.

One honest footnote: if delta u ever lands on exactly zero, the cancelling step breaks, and a fully rigorous proof handles that case separately. But the heart of the idea is complete. The total rate is the product of the rates along the chain.

Let us test it on y equals the sine of x squared. On the left, a parabola. On the right, a sine wave.

The inner machine is u equals x squared. The outer machine is y equals the sine of u.

The inner rate is two x. The outer rate is the cosine of u. Multiply them, put x squared back in for u, and we get: the derivative equals two x times the cosine of x squared.

But is the formula telling the truth? Let us check at x equals one.

At x equals one, the inner rate is two, so the first machine stretches every tiny nudge by a factor of two. The outer rate is the cosine of one, which is about zero point five four. Multiply: two times zero point five four, about one point zero eight.

Now the brute force check, with no formula at all. Nudge x from one to one point zero zero one. Watch x squared move from one to one point zero zero two zero zero one, about twice the nudge. Then the sine of that moves from about zero point eight four one five to about zero point eight four two six, a change of roughly zero point zero zero one zero eight.

Divide that change by our nudge of zero point zero zero one, and we get about one point zero eight. The formula and the brute force agree.

A common mistake is to write only the cosine of x squared, forgetting the inner rate. That means forgetting the first gear.

Now, back to our neural network. Picture three layers of glowing nodes joined by thousands of thin lines.

One weight sits deep inside, on a single line. It shapes a neuron's input. That passes through an activation function to become the neuron's output. That output feeds the next layer, which finally produces a prediction. The prediction is compared to the truth, giving one number called the loss, which measures how wrong the network is.

That is a long chain of functions, each one inside the next. Asking how the loss changes when we nudge that one weight is a chain rule problem, with a rate at every link.

Backpropagation simply walks backward from the loss, multiplying one local rate at a time, like gears turning in reverse. When it arrives at the weight, the product tells it exactly which way to turn and by how much. Then it does the same for every other weight, billions of times.

There is no new mathematics hiding inside. It is the chain rule, applied at enormous scale.

So the next time you meet the derivative of y with respect to x equals the derivative of y with respect to u, times the derivative of u with respect to x, do not see symbols. See gears.

A nudge enters at one end, gets stretched or squeezed by every link along the way, and what comes out is the product of all those stretches.

That is why a shadow, a bank balance, and a billion-dial neural network can all be understood by the same idea.

In the next video, we will watch backpropagation run on a real network, one step at a time. See you there.