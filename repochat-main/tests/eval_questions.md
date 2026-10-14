# Evaluation Questions (sample_repo)

Use these to manually sanity-check Phase 1, and later as the basis for the
automated Phase 5 benchmark (Recall@5, citation accuracy, faithfulness).

1. Where is authentication implemented?
2. Where is the JWT token generated?
3. Which function verifies passwords?
4. What calls authenticate_user()?
5. What happens when POST /login is called?
6. Which database table stores users?
7. What happens if the database connection fails?
8. What files would be affected by changing UserService?
9. Explain the architecture of this project.
10. Find the bug in the password hashing logic.
11. Where is the database connection created?
12. Which functions call verify_password()?
13. What database tables does this project use?
14. Where is the users table schema defined?
15. What does handle_register do?
16. What does handle_refresh_token currently do?
17. Which module does UserService depend on?
18. What happens when a new user registers with a username that's taken?
19. Where is the JWT_SECRET defined?
20. Is there a salt used when hashing passwords?
21. What tests exist for the authentication flow?
22. What does test_verify_password_rejects_wrong_password check?
23. Which file defines the orders table?
24. What fields does the orders table have?
25. If I change authenticate_user(), what could be affected?
26. Which endpoints depend on the database connection module?
27. What does get_connection() return?
28. Show me the files related to user registration.
29. Why might login fail even with a correct password?
30. What's the relationship between UserService and the auth module?
31. Explain how user registration works end-to-end.
32. Which function issues the actual SQL insert for a new user?
