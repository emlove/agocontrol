package com.agocontrol.agocontrol;

public class Global {

	public static final boolean DEBUG = true; // Java does not have the concept of conditional compilation
	                                          // like C/C++ #ifdef. However, if a "standards compliant"
	                                          // java compiler encounters a statement that will always evaluate
	                                          // to false, it should be optimized out.  So this is the closest
											  // java equivalent way to do it
	
	private Global() {} //utility class pattern - private constructor
}
