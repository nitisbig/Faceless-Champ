This is a cheetah at full sprint. But slow it down, and something strange appears. Every video is just a stack of flat pictures.

Stack them one behind another, and time becomes a direction you can point to. Playing the video is simply sliding a flat slice through a solid block.

Now take a cube. We only ever see its flat shadow, yet our brains understand it instantly. So if a cube casts a two dimensional shadow, what casts a three dimensional one? An object from the fourth dimension. And this is what its shadow looks like.

By the end of this video, you will not just see this shape. You will understand it. Using vectors and a little linear algebra, we will count its corners, measure its diagonal, slice it, and rotate it in a way that is impossible in our world.

So first, what actually is a dimension?

Imagine an ant on a wire. To say where it is, you need one number: how far along the wire. One dimension. Put the ant on a table, and you need two: how far right, and how far forward. Let it fly into the room, and you need a third: how high.

So a dimension is simply the number of independent numbers you need to describe a position. We write those numbers as a vector. The vector three, two, five means three steps along x, two along y, and five along z. Each direction has its own unit arrow, called a basis vector, and every point is just a mix of those arrows.

Now here is the trick. Nothing forces us to stop at three. Add a fourth number, w, and a fourth arrow, at right angles to x, y and z all at once. You cannot picture where it points. But you can add it, scale it, and measure it, exactly like the others. The algebra does not even flinch.

You have already seen a space like this. Every pixel in the cheetah video needs three numbers: its x, its y, and its frame. The video is a three dimensional block, where the third direction is time. Add one more number, and you have four dimensions.

So let's build a four dimensional object, with one simple move: drag a shape along a new direction.

Drag a point along x, and you get a line segment with two ends. Drag the segment along y, and you get a square with four corners. Drag the square along z, and you get a cube with eight corners. Now drag the cube along w, the direction we cannot see. The result is a tesseract, a hypercube.

Every drag copies the shape, so the corners double. One, two, four, eight, sixteen. A cube in n dimensions has two to the power n corners.

Edges follow a pattern too. You keep the edges of both copies, and add one new edge for every corner that moved. A cube has two times four, plus four, which is twelve edges. A tesseract has two times twelve, plus eight, which is thirty two edges. It also has twenty four square faces, and eight cubes as its walls.

In coordinates, every corner is made of zeros and ones. Zero, zero, zero, zero is one corner. One, one, one, one is the opposite corner. Sixteen combinations, sixteen corners.

And we can measure it. By Pythagoras, the diagonal of a unit square is the square root of one plus one, which is the square root of two. A cube adds one more term, giving the square root of three. A tesseract adds one more, giving the square root of four. Exactly two. The length of any vector is the square root of the sum of its squared parts, whether it has two parts or two thousand.

But how would we actually see a four dimensional object? Only in pieces. To understand why, shrink down by one dimension.

Imagine a flat creature living on a sheet of paper. A ball falls through its world. The creature never sees a ball. It sees a dot appear, grow into a circle, shrink, and vanish. Each moment is one slice of the sphere.

One level up, a four dimensional ball passing through our space would look like a tiny sphere appearing from nowhere, swelling, shrinking, and disappearing. That is exactly what playing the cheetah video did. Each frame was one slice of a three dimensional block.

Slices of a tesseract are even stranger. Push it through corner first, and you first see a tiny tetrahedron, a triangular pyramid. It grows, its corners get clipped, and at the middle it becomes a perfect octahedron, like two pyramids glued base to base. Then it all plays in reverse. Same object, completely different slices, depending only on its angle.

Slices show one piece at a time. Shadows show everything at once. And a shadow is pure linear algebra.

Shine a light straight down on a cube, and the shadow forgets the height. Every point x, y, z lands at x, y. That forgetting is a matrix that keeps x, keeps y, and multiplies z by zero. From four dimensions to three, a three by four matrix keeps x, y and z, and drops w.

But a straight shadow stacks corners on top of each other, so we use perspective, the same rule your eyes use. Farther things look smaller. Place a camera out along w. Each point is scaled by the camera distance, divided by the camera distance minus w. Points with a large w come closer and grow. Points with a small w move away and shrink.

So the eight near corners form a big cube, and the eight far corners form a small cube. Join them along w, and you get the famous picture: a cube inside a cube. The six lopsided shapes between them are real cubes, seen in four dimensional perspective.

Now let's make it move. In two dimensions, rotating by an angle theta is a two by two matrix. The new x is cosine theta times x, minus sine theta times y. The new y is sine theta times x, plus cosine theta times y.

In three dimensions, we say an object rotates around an axis. But when a cube spins around the vertical axis, its height never changes. Only the other two coordinates mix. So rotation really happens in a plane. The axis is just what is left over.

That idea unlocks four dimensions. With three axes, there are three planes: x y, x z, and y z. With four axes, there are six: x y, x z, x w, y z, y w, and z w. The formula is n times n minus one, divided by two. Four times three, divided by two, is six ways to rotate.

Let's rotate in the z w plane. The matrix leaves x and y alone, and mixes z with w using the same cosine and sine. Watch the shadow. The inner cube grows, the outer cube shrinks, and they pass through each other. The tesseract seems to turn inside out. But nothing bends. The matrix is orthogonal, its determinant is one, and every edge keeps its length. It is a rigid object, turning in a direction we can only see as a shadow.

Four dimensions even allow a double rotation, in the x y plane and the z w plane at the same time. No axis is left over, and the only point that stays still is the very center.

So is any of this real? We may never step into a fourth direction of space. But its mathematics is everywhere. Physics treats time as a fourth coordinate of spacetime. Game engines and spacecraft use quaternions, numbers with four parts, to rotate objects smoothly. And inside a model like ChatGPT, a single word is a vector with thousands of dimensions, measured and projected with the same tools we just used on a tesseract.

That is the real lesson. Your eyes stop at three dimensions. Linear algebra does not.

Let's recap. A dimension is the number of independent numbers needed to describe a position. Adding a fourth number creates a fourth direction. Dragging a cube along it builds a tesseract, with sixteen corners, thirty two edges, and a long diagonal of exactly two. We see it through slices, like frames of a video, and through shadows, which are projection matrices. And rotation happens in planes, giving four dimensions six ways to turn.

So the next time you watch a video, remember. You are already sliding through a higher dimension, one frame at a time.

If this made the fourth dimension a little less mysterious, subscribe for more complex math, made visual. See you in the next dimension.
