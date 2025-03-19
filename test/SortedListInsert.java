/**
 * Copyright (c) 2011, Regents of the University of California
 * All rights reserved.
 * <p/>
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * <p/>
 * 1. Redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer.
 * <p/>
 * 2. Redistributions in binary form must reproduce the above
 * copyright notice, this list of conditions and the following
 * disclaimer in the documentation and/or other materials provided
 * with the distribution.
 * <p/>
 * 3. Neither the name of the University of California, Berkeley nor
 * the names of its contributors may be used to endorse or promote
 * products derived from this software without specific prior written
 * permission.
 * <p/>
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 * COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
 * INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 */

//package edu.berkeley.cs.wise.benchmarks;

//import edu.berkeley.cs.wise.concolic.Concolic;

/**
 * @author Jacob Burnim <jburnim@cs.berkeley.edu>
 * Modified by Daniel Koh <daniel.koh@student.manchester.ac.uk>
 */

 public class SortedListInsert {

    // This is a counter to keep track of the number of times the insert method is called.
    // Intuitively, we utilise this to determine if this is a valid test case that invokes the worst-case scenario
    private static int insertCallCount = 0;

    private static class List {
        private int x;
        private List next;

        private static final int SENTINEL = Integer.MAX_VALUE;

        private List(int x, List next) {
            this.x = x;
            this.next = next;
        }

        public List() {
            this(SENTINEL, null);
        }
        
        public void insertMask(int data) {
          if (data > this.x) {
              next.insertMask(data);
          } else {
              next = new List(x, next);
              x = data;
          }
      }

        public void insert(int data) {
            insertCallCount++;
            if (data > this.x) {
                next.insert(data);
            } else {
                next = new List(x, next);
                x = data;
            }
        }
    }

    public static void main(String[] args) {
        // The first argument is the number of elements to build initially.
        int N = Integer.parseInt(args[0]);
        // The second argument is the data element to insert after building the list.
        int data = Integer.parseInt(args[1]);
        
        // Build the initial sorted list with values -1,0, 1, ..., N-1.
        List list = new List();
        for (int i = 0; i < N; i++) {
            list.insertMask(i);
        }
        
        // Insert the provided data element.
        list.insert(data);

        // Print the number of times the insert method was called.
        System.out.println(insertCallCount);
        
    }
}